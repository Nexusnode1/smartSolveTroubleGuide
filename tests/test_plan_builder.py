"""End-to-end plan building over the twenty official rows."""

import re

import pytest

from app.models.official_schema import ContextDeeplinkResponse
from app.services.plan_builder import PlanBuilder

RANK = {"auto": 0, "manual": 1, "critical": 2}
GOAL = re.compile(r"^Follow these steps to perform this .+ (?:Troubleshooting|Configuration)$")
URL = re.compile(r"https?://|www\.", re.IGNORECASE)


@pytest.fixture(scope="module")
def builder(catalog):
    return PlanBuilder(catalog)


@pytest.fixture(scope="module")
def builds(builder, siis_rows):
    result = {}
    for row in siis_rows:
        siis = row["siis_response"]
        result[row["id"]] = builder.build(row["original_query"], siis["content"], siis["title"])
    return {row_id: build for row_id, build in result.items() if build is not None}


def _actions(build):
    return build.response["contexts"][0]["actions"]


def _groups(build):
    return [group for action in _actions(build) for group in action["stepGroups"]]


def test_most_rows_build_and_every_built_plan_is_rule_valid(builds):
    assert len(builds) >= 12
    for row_id, build in builds.items():
        assert build.errors == (), row_id


def test_built_plans_satisfy_the_official_schema(builds):
    for build in builds.values():
        ContextDeeplinkResponse.model_validate(build.response)


def test_goal_title_score_and_variations(builds):
    for build in builds.values():
        context = build.response["contexts"][0]
        assert GOAL.match(context["goal"])
        assert 2 <= len(context["title"].split()) <= 3
        assert 0.0 <= context["score"] <= 1.0
        assert 8 <= len(build.query_variations) <= 10


def test_actions_are_ordered_auto_manual_critical(builds):
    for build in builds.values():
        ranks = [RANK[action["category"]] for action in _actions(build)]
        assert ranks == sorted(ranks)


def test_only_auto_actions_carry_deeplinks(builds):
    for build in builds.values():
        for action in _actions(build):
            for group in action["stepGroups"]:
                assert (group["actionableDeeplink"] is not None) == (action["category"] == "auto")


def test_every_deeplink_is_verbatim_from_the_catalog(builds, catalog):
    actionable = {entry["deeplink"] for entry in catalog}
    validation = {entry["validation"]["deeplink"] for entry in catalog if entry.get("validation")}
    for build in builds.values():
        for group in _groups(build):
            if group["actionableDeeplink"]:
                assert group["actionableDeeplink"]["deeplink"] in actionable
            if group["validationDeeplink"]:
                assert group["validationDeeplink"]["deeplink"] in validation


def test_no_urls_in_any_plan_text(builds):
    for build in builds.values():
        context = build.response["contexts"][0]
        texts = [context["goal"], context["title"]]
        for action in context["actions"]:
            texts += [action["actionName"], action["description"]]
            texts += [step for group in action["stepGroups"] for step in group["steps"]]
        assert not any(URL.search(text) for text in texts)


def test_touchscreen_plan_maps_screens_exactly(builds, catalog_by_id):
    links = {g["actionableDeeplink"]["deeplink"] for g in _groups(builds["row_21"]) if g["actionableDeeplink"]}
    assert catalog_by_id["DL-0126"]["deeplink"] in links  # enable Touch sensitivity
    assert catalog_by_id["DL-0125"]["deeplink"] in links  # disable Touch sensitivity
    assert catalog_by_id["DL-0169"]["deeplink"] in links  # Navigation bar


def test_email_plan_links_wifi_first_and_ends_critical(builds, catalog_by_id):
    actions = _actions(builds["row_1"])
    group = actions[0]["stepGroups"][0]
    assert actions[0]["category"] == "auto"
    assert group["actionableDeeplink"]["deeplink"] == catalog_by_id["DL-0313"]["deeplink"]
    assert group["validationDeeplink"]["deeplink"] == catalog_by_id["DL-0313"]["validation"]["deeplink"]
    assert actions[-1]["category"] == "critical"


def test_unrelated_query_is_refused(builder, siis_rows):
    siis = siis_rows[1]["siis_response"]
    assert builder.build("best pasta recipe", siis["content"], siis["title"]) is None


def test_unindexed_settings_screen_uses_the_placeholder(builder):
    build = builder.build("check storage settings", "## Check storage\nGo to Settings. Tap Storage.", "Storage help")
    assert build is not None and build.errors == ()
    action = build.response["contexts"][0]["actions"][0]
    link = action["stepGroups"][0]["actionableDeeplink"]
    assert action["category"] == "auto"
    assert link["deeplink"] == "bixby://dummy_positive"
    assert link["description"] == "Opens the Storage Settings screen"
    assert link["message"] == "Open the Storage screen in Settings"


def test_building_is_deterministic(builder, siis_rows):
    siis = siis_rows[0]["siis_response"]
    first = builder.build(siis_rows[0]["original_query"], siis["content"], siis["title"])
    second = builder.build(siis_rows[0]["original_query"], siis["content"], siis["title"])
    assert first == second

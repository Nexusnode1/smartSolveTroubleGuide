"""Steps map to catalog entries by the exact Settings label they tap."""

import pytest

from app.services.key_matcher import DUMMY_URI, KeyIndex, normalize_label, tap_targets


def test_tap_targets_skip_the_settings_root():
    assert tap_targets(["Go to Settings.", "Tap Connections.", "Tap Wi-Fi."]) == ["Connections", "Wi-Fi"]


def test_tap_targets_trim_trailing_clauses():
    assert tap_targets(["Tap the switch next to Touch sensitivity to disable it."]) == ["Touch sensitivity"]


def test_tap_targets_ignore_action_buttons():
    assert tap_targets(["Tap Clear cache.", "Tap OK.", "Tap Restart again to confirm.", "Tap Safe mode."]) == []


def test_normalize_label_ignores_case_and_punctuation():
    assert normalize_label("Wi-Fi") == normalize_label("wi fi") == "wi fi"


@pytest.fixture(scope="module")
def index(catalog):
    return KeyIndex(catalog)


def test_wifi_opens_the_plain_screen_by_default(index, catalog_by_id):
    choice = index.find(["Go to Settings.", "Tap Connections.", "Tap Wi-Fi."], "")
    assert choice.entry["id"] == "DL-0313"
    assert choice.entry["deeplink"] == catalog_by_id["DL-0313"]["deeplink"]


@pytest.mark.parametrize("context, expected", [("Enable Wi-Fi", "DL-0574"), ("Disable Wi-Fi", "DL-0573")])
def test_toggle_direction_follows_the_text(index, context, expected):
    assert index.find(["Tap Wi-Fi."], context).entry["id"] == expected


def test_touch_sensitivity_on_and_off(index):
    steps = ["Tap Display.", "Tap the switch next to Touch sensitivity."]
    assert index.find(steps, "enable it").entry["id"] == "DL-0126"
    assert index.find(steps, "disable it").entry["id"] == "DL-0125"


def test_unindexed_labels_do_not_match(index):
    assert index.find(["Tap Safe mode."], "") is None
    assert index.find(["Tap Storage."], "") is None


def test_the_placeholder_is_never_a_match(index, catalog):
    for entry in catalog:
        choice = index.find([f"Tap {entry.get('message') or 'Nothing'}."], "")
        assert choice is None or choice.entry["deeplink"] != DUMMY_URI

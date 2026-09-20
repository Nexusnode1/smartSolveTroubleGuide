"""End-to-end deterministic engine tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.services.troubleshooting_engine import TroubleshootingEngine


def _catalog() -> dict:
    configured = os.environ.get("DEEPLINKS_PATH")
    if configured and Path(configured).exists():
        return json.loads(Path(configured).read_text())
    return {"deeplinks": [
        {"id": "slow", "deeplink": "bixby://masked/slow", "description": "Diagnoses slow device performance.", "message": "Diagnose Slow Performance", "qna_description": "Improves device speed.", "originalType": "onClickURL"},
        {"id": "camera", "deeplink": "bixby://masked/camera", "description": "Opens camera access settings.", "message": "View Camera access", "qna_description": "Controls camera access.", "originalType": "onClickURL"},
    ]}


@pytest.fixture(scope="module")
def engine() -> TroubleshootingEngine:
    return TroubleshootingEngine(_catalog())


@pytest.mark.parametrize("query", [
    "My battery drains very quickly", "My phone gets hot", "My phone is slow",
    "My camera is not working", "My battery is dying after the update",
    "bro my phone is getting crazy hot", "my battry is draining fst", "phone problem",
    "unrelated query about cooking", "no valid catalog match",
])
def test_real_query_shapes_return_validated_responses(engine: TroubleshootingEngine, query: str) -> None:
    run = engine.troubleshoot_with_debug(query)
    assert run.validation.valid is True
    assert run.response["contexts"]
    assert 0.0 <= run.response["contexts"][0]["score"] <= 1.0
    assert run.debug["validation"]["valid"] is True
    serialized = json.dumps(run.response)
    assert "http://" not in serialized and "https://" not in serialized and "www." not in serialized


def test_deterministic_output_and_debug(engine: TroubleshootingEngine) -> None:
    first = engine.troubleshoot_with_debug("My phone is slow")
    second = engine.troubleshoot_with_debug("My phone is slow")
    assert first.response == second.response
    assert first.debug == second.debug


def test_manual_and_critical_scenarios_have_correct_categories(engine: TroubleshootingEngine) -> None:
    manual = engine.troubleshoot_with_debug("please remove the case manually")
    assert manual.response["contexts"][0]["actions"][0]["category"] == "manual"
    assert manual.response["contexts"][0]["actions"][0]["stepGroups"][0]["actionableDeeplink"] is None

    critical = engine.troubleshoot_with_debug("restart my phone")
    assert critical.response["contexts"][0]["actions"][0]["category"] == "critical"


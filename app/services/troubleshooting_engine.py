"""Deterministic end-to-end troubleshooting pipeline.

The engine composes the existing stages without exposing their internal
evidence in the official response.  A separate ``EngineRun`` object is
available for benchmarking and debugging.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

from app.models.schemas import QueryEnrichmentResult
from app.services.action_ordering import order_actions
from app.services.deeplink_mapper import map_action
from app.services.hybrid_retriever import HybridRetriever
from app.services.plan_validator import PlanValidationResult, validate_plan
from app.services.query_enrichment import QueryEnricher
from app.services.screen_resolver import resolve_action
from app.services.structure_extraction import extract_structure


_CATALOG_FIELDS = (
    "title", "description", "message", "qna_description", "text",
    "target_screen", "screen", "screen_name", "target", "intent", "category",
    "keywords", "query", "label", "name", "control_type", "originalType",
)
_RETRIEVAL_FIELDS = (
    "description", "message", "qna_description", "originalType", "target_screen",
)
_TOKEN = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*", re.IGNORECASE)
_GENERIC = frozenset("phone mobile device problem issue help thing something my very".split())
_SYMPTOM_MODIFIERS = frozenset("very extremely crazy quickly rapidly constantly getting after update".split())
_CRITICAL_QUERY = re.compile(
    r"\b(?:restart|reboot|reset|factory\s+reset|firmware|safe\s+mode|wipe|erase|recovery)\b",
    re.IGNORECASE,
)
_MANUAL_QUERY = re.compile(r"\b(?:manually|manual|physically|offline|remove\s+the\s+case)\b", re.IGNORECASE)


@dataclass(frozen=True)
class EngineRun:
    """Official response plus non-schema stage evidence."""

    response: dict[str, Any]
    debug: Mapping[str, Any]
    validation: PlanValidationResult


def _entries(catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    """Copy catalog records and add only a derived screen label.

    The source records and URI strings are never mutated.  ``message`` is the
    catalog's own physical-feature label when no explicit screen field exists.
    """
    if catalog is None:
        return []
    raw: Iterable[Mapping[str, Any]]
    if isinstance(catalog, Mapping):
        values = catalog.get("deeplinks", [])
        raw = values if isinstance(values, list) else []
    else:
        raw = catalog
    result: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("deeplink"), str):
            continue
        copied = dict(entry)
        if not any(isinstance(copied.get(field), str) and copied[field].strip() for field in ("target_screen", "screen", "screen_name", "target")):
            message = copied.get("message")
            if isinstance(message, str) and message.strip():
                copied["target_screen"] = message.strip()
        result.append(copied)
    return result


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return dict(value)


def _variations(enriched: QueryEnrichmentResult) -> list[str]:
    """Produce the required 8–10 distinct deterministic query variations."""
    core = enriched.core_intent or enriched.normalized_query
    candidates = [
        enriched.original_query,
        enriched.normalized_query,
        core,
        f"troubleshoot {core}",
        f"help with {core}",
        f"problem with {core}",
        f"how to fix {core}",
        f"resolve {core}",
        f"device issue {core}",
        f"settings help {core}",
    ]
    return list(dict.fromkeys(item.strip() for item in candidates if item.strip()))[:10]


def _title(structure: Any) -> str:
    words = [word for word in _TOKEN.findall(structure.core_intent) if word.lower() not in {"help", "problem", "issue"}]
    words = words[:3] or ["Troubleshooting", "guidance"]
    return " ".join([words[0].capitalize(), *[word.lower() for word in words[1:]]])


def _query_terms(structure: Any) -> set[str]:
    return {word.lower() for word in _TOKEN.findall(structure.normalized_query) if word.lower() not in _GENERIC}


def _candidate_has_query_signal(structure: Any, entry: Mapping[str, Any]) -> bool:
    """Reject generic semantic collisions unless a symptom/entity is present."""
    query_terms = _query_terms(structure)
    metadata = " ".join(str(entry.get(field, "")) for field in _RETRIEVAL_FIELDS).lower()
    metadata_terms = set(_TOKEN.findall(metadata))
    entities = {word.lower() for word in structure.entities}
    symptoms = {
        word.lower()
        for symptom in structure.symptoms
        for word in _TOKEN.findall(symptom)
        if word.lower() not in entities
        and word.lower() not in _GENERIC
        and word.lower() not in _SYMPTOM_MODIFIERS
    }
    if symptoms:
        return bool(symptoms & metadata_terms)
    return bool(entities & metadata_terms and query_terms & metadata_terms)


def _fallback_action(category: str = "manual") -> dict[str, Any]:
    return {
        "actionName": "Troubleshooting clarification",
        "description": "It will clarify the affected troubleshooting issue",
        "stepGroups": [{"steps": ["Describe the affected feature."], "actionableDeeplink": None}],
        "category": category,
    }


class TroubleshootingEngine:
    """Compose enrichment through validation without caching or API concerns."""

    def __init__(self, catalog: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None = None) -> None:
        self.catalog = _entries(catalog)
        self.retriever = (
            HybridRetriever(self.catalog, metadata_fields=_RETRIEVAL_FIELDS)
            if self.catalog
            else None
        )
        self.enricher = QueryEnricher()

    def troubleshoot(self, query: str) -> dict[str, Any]:
        """Return only the official-schema response from a validated run."""
        return self.troubleshoot_with_debug(query).response

    def troubleshoot_with_debug(self, query: str) -> EngineRun:
        """Run every pipeline stage and retain internal evidence separately."""
        enriched = self.enricher.enrich(query)
        structure = extract_structure(enriched)
        variations = _variations(enriched)
        intent_context = {
            "possible_intents": list(structure.possible_intents),
            "ambiguous": structure.is_ambiguous,
            "confidence": 0.0 if structure.is_ambiguous else 1.0,
        }
        retrieval_results = self.retriever.search(enriched.core_intent, top_k=5) if self.retriever else []
        selected = retrieval_results[0] if retrieval_results else None
        clear_match = bool(
            selected
            and selected.hybrid_score >= 0.40
            and (len(retrieval_results) == 1 or selected.hybrid_score - retrieval_results[1].hybrid_score > 0.05)
            and _candidate_has_query_signal(structure, selected.entry)
            and not structure.is_ambiguous
        )
        mapped = None
        resolution = None
        action_dict: dict[str, Any]
        if clear_match and selected is not None:
            target = selected.entry.get("target_screen") or selected.entry.get("message")
            resolution = resolve_action({"target_screen": target}, [selected.entry])
            mapped = map_action({"target_screen": target}, [selected.entry]) if resolution.resolved else None
        critical = bool(_CRITICAL_QUERY.search(enriched.normalized_query))
        manual = bool(_MANUAL_QUERY.search(enriched.original_query))
        if mapped is not None and mapped.resolved and mapped.deeplink:
            entry = selected.entry
            link: dict[str, Any] = {
                "deeplink": mapped.deeplink,
                "description": entry.get("description", ""),
                "message": entry.get("message", ""),
                "originalType": entry.get("originalType"),
            }
            validation = entry.get("validation")
            group: dict[str, Any] = {"steps": [f"Open {mapped.target_screen}."], "actionableDeeplink": link}
            if isinstance(validation, Mapping) and isinstance(validation.get("deeplink"), str) and isinstance(validation.get("key"), str):
                group["validationDeeplink"] = {key: validation[key] for key in ("deeplink", "key", "resultType", "condition", "value") if key in validation}
            action_dict = {
                "actionName": str(mapped.target_screen),
                "description": "It will open the relevant Settings screen",
                "stepGroups": [group],
                "category": "critical" if critical else "auto",
            }
        else:
            action_dict = _fallback_action("critical" if critical and not manual else "manual")

        ordered = order_actions([action_dict])
        actions = [decision.action for decision in ordered]
        response = {
            "contexts": [{
                "goal": f"Follow these steps to troubleshoot {enriched.core_intent or 'the request'}",
                "title": _title(structure),
                "score": float(mapped.confidence if mapped and mapped.resolved else 0.0),
                "actions": actions,
            }]
        }
        payload = {**response, "query_variations": variations}
        result = validate_plan(payload, self.catalog)
        if not result.valid:
            fallback_response = {
                "contexts": [{
                    "goal": "Follow these steps to clarify the troubleshooting request",
                    "title": "Troubleshooting guidance",
                    "score": 0.0,
                    "actions": [_fallback_action("manual")],
                }]
            }
            result = validate_plan({**fallback_response, "query_variations": variations}, self.catalog)
            response = fallback_response
        debug = {
            "query_enrichment": _model_dump(enriched),
            "structure": _model_dump(structure),
            "intent_context": intent_context,
            "retrieval": [
                {"id": item.entry.get("id"), "hybrid_score": item.hybrid_score, "bm25_score": item.bm25_score, "dense_score": item.dense_score}
                for item in retrieval_results
            ],
            "screen_resolution": resolution.model_dump(mode="json") if resolution is not None else None,
            "deeplink_mapping": mapped.__dict__ if mapped is not None else None,
            "ordering": [{"category": decision.category, "priority": decision.priority, "reason": decision.reason} for decision in ordered],
            "validation": {"valid": result.valid, "errors": result.errors},
        }
        return EngineRun(response=response, debug=debug, validation=result)

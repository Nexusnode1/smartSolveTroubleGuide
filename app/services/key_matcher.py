"""Match SIIS steps to catalog deeplinks by the exact UI label they tap.

Catalog ``validation.key`` values are the literal Settings labels ("Wi-Fi",
"Navigation bar"). The URI itself is never a match feature and is copied
verbatim from the matched entry.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

DUMMY_URI = "bixby://dummy_positive"

_TAP = re.compile(
    r"\b(?i:tap|select|touch|choose|open)(?:\s+(?i:and\s+hold))?(?:\s+(?i:on))?"
    r"(?:\s+(?i:the))?(?:\s+(?i:switch\s+next\s+to))?"
    r"\s+([A-Z][A-Za-z0-9+\-/()' ]*?)(?=\s*(?:[,.;:]|$))"
)
_TRIM = re.compile(
    r"\s+(?:to|again|for|if|when|and|then|in|on|from|at|until|so|because)\b.*$", re.IGNORECASE
)
_NOT_A_SCREEN = frozenset(
    {
        "ok", "settings", "restart", "reset", "delete all", "clear cache", "clear data",
        "safe mode", "power off", "power", "recents", "home",
    }
)
_TURN_OFF = re.compile(r"\b(?:turn\s+off|disable|switch\s+off|toggle\s+off)\b", re.IGNORECASE)
_TURN_ON = re.compile(
    r"\b(?:turn\s+on|enable|switch\s+on|toggle\s+on|switch\s+next\s+to)\b", re.IGNORECASE
)


def normalize_label(text: str) -> str:
    """Lower-case a UI label and collapse punctuation for exact comparison."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def tap_targets(steps: Iterable[str]) -> list[str]:
    """Return the UI labels tapped by ``steps`` in order, excluding action buttons."""
    targets: list[str] = []
    for step in steps:
        for match in _TAP.finditer(step):
            label = _TRIM.sub("", match.group(1)).strip()
            if label and normalize_label(label) not in _NOT_A_SCREEN:
                targets.append(label)
    return targets


@dataclass(frozen=True)
class DeeplinkChoice:
    """A catalog entry chosen for a step group and the label that matched it."""

    entry: Mapping[str, Any]
    target: str


class KeyIndex:
    """Index of catalog entries by their exact Settings label."""

    def __init__(self, catalog: Iterable[Mapping[str, Any]]) -> None:
        self._by_key: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for entry in catalog:
            validation = entry.get("validation")
            key = validation.get("key") if isinstance(validation, Mapping) else None
            if isinstance(key, str) and entry.get("deeplink") != DUMMY_URI:
                self._by_key[normalize_label(key)].append(entry)

    def find(self, steps: Sequence[str], context: str) -> DeeplinkChoice | None:
        """Pick the entry for the last tapped label that exists in the catalog."""
        for target in reversed(tap_targets(steps)):
            entries = self._by_key.get(normalize_label(target))
            if entries:
                return DeeplinkChoice(_pick(entries, context), target)
        return None


def _pick(entries: Sequence[Mapping[str, Any]], context: str) -> Mapping[str, Any]:
    """Prefer the toggle direction the text asks for, else the plain open entry."""
    order = ["onClickURL", "onURL", "updateURL", "offURL"]
    if _TURN_OFF.search(context):
        order.insert(0, "offURL")
    elif _TURN_ON.search(context):
        order.insert(0, "onURL")
    for original_type in order:
        for entry in entries:
            if entry.get("originalType") == original_type:
                return entry
    return entries[0]

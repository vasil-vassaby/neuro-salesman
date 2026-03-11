from __future__ import annotations

from typing import Optional

from .rules import classify_keywords
from .types import IntentType


def detect_intent(
    text: str,
    *,
    state_flow: Optional[str] = None,
) -> IntentType:
    """Detect high-level intent for a user message.

    Skeleton version for Core v2. It exposes a typed contract but does
    not integrate with the existing project or perform complex logic.
    """

    _ = state_flow
    _normalized = (text or "").strip().casefold()
    keyword_intent = classify_keywords(_normalized)
    if keyword_intent is not None:
        return keyword_intent
    return IntentType.OTHER


__all__ = ["detect_intent"]


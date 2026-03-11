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

    Minimal Core v2 logic:
    - explicit commands (/start, /help, /reset)
    - keyword rules (согласен, записаться, цена)
    - everything else -> FREE_QUESTION or OTHER
    """

    _ = state_flow
    normalized = (text or "").strip().casefold()
    if not normalized:
        return IntentType.OTHER

    if normalized.startswith("/start"):
        return IntentType.START
    if normalized.startswith("/help"):
        return IntentType.HELP
    if normalized.startswith("/reset"):
        return IntentType.RESET

    keyword_intent = classify_keywords(normalized)
    if keyword_intent is not None:
        return keyword_intent

    return IntentType.FREE_QUESTION


__all__ = ["detect_intent"]


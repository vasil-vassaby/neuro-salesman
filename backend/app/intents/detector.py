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

    - does not mutate state
    - does not contain business logic
    - only classifies the message
    """

    normalized = (text or "").strip().casefold()
    if not normalized:
        return IntentType.other

    # explicit commands first
    if normalized.startswith("/start"):
        return IntentType.start
    if normalized.startswith("/help"):
        return IntentType.help
    if normalized.startswith("/reset"):
        return IntentType.reset

    # keyword rules (booking, price, faq-like, reschedule, etc.)
    keyword_intent = classify_keywords(normalized)
    if keyword_intent is not None:
        return keyword_intent

    # anything meaningful but without known keywords — free question
    return IntentType.free_question


__all__ = ["detect_intent"]


from __future__ import annotations

from typing import Optional

from .types import IntentType


def classify_keywords(text: str) -> Optional[IntentType]:
    """Classify text by simple keyword rules.

    Minimal Core v2 logic for the first iteration. It must remain
    side-effect free and not depend on old handlers.
    """

    if not text:
        return None

    normalized = text.strip().casefold()

    if "согласен" in normalized or "согласна" in normalized:
        return IntentType.CONSENT_ACCEPT

    if "записать" in normalized or "записаться" in normalized:
        return IntentType.BOOKING
    if "запись" in normalized:
        return IntentType.BOOKING

    if "цена" in normalized or "стоимость" in normalized:
        return IntentType.PRICE

    return None


__all__ = ["classify_keywords"]


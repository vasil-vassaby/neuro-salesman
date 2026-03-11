from __future__ import annotations

from typing import Optional

from .types import IntentType


def classify_keywords(text: str) -> Optional[IntentType]:
    """Classify text by simple keyword rules.

    This is a placeholder for Core v2 specific rules. It must remain
    side-effect free and not depend on old handlers.
    """

    return None


__all__ = ["classify_keywords"]


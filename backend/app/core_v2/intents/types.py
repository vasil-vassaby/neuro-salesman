from __future__ import annotations

from enum import Enum


class IntentType(str, Enum):
    """High-level user intents understood by Core v2."""

    START = "start"
    HELP = "help"
    RESET = "reset"
    BOOKING = "booking"
    PRICE = "price"
    FAQ = "faq"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    HANDOFF = "handoff"
    FREE_QUESTION = "free_question"
    OTHER = "other"


__all__ = ["IntentType"]


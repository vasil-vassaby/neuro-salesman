from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ConversationState:
    """Minimal Core v2 dialog state snapshot.

    This state is intentionally transport-agnostic and can be used by
    Telegram, web and other channels.
    """

    flow: Optional[str]
    step: Optional[str]
    pd_consent: bool
    active_booking_id: Optional[str]
    handoff_mode: bool
    goal: Optional[str]
    format: Optional[str]
    time_pref: Optional[str]
    slot_id: Optional[str]


__all__ = ["ConversationState"]


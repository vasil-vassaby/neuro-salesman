from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..models import Conversation


@dataclass
class ConversationState:
    flow: str
    step: int
    pd_consent: bool
    goal: str | None
    format: str | None
    time_pref: str | None
    slot_id: str | None
    active_booking_id: str | None
    handoff_mode: bool

    @classmethod
    def from_raw(cls, raw: Dict[str, Any] | None) -> "ConversationState":
        if not isinstance(raw, dict):
            raw = {}
        flow = raw.get("flow") or "other"
        step_raw = raw.get("step") or 0
        try:
            step = int(step_raw)
        except (TypeError, ValueError):
            step = 0
        pd_consent = bool(raw.get("pd_consent") or False)
        goal = raw.get("goal")
        fmt = raw.get("format")
        time_pref = raw.get("time_pref")
        slot_id = raw.get("slot_id")
        active_booking_id = raw.get("active_booking_id")
        handoff_mode = bool(raw.get("handoff_mode") or False)
        return cls(
            flow=flow,
            step=step,
            pd_consent=pd_consent,
            goal=goal,
            format=fmt,
            time_pref=time_pref,
            slot_id=slot_id,
            active_booking_id=active_booking_id,
            handoff_mode=handoff_mode,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow": self.flow,
            "step": int(self.step),
            "goal": self.goal,
            "format": self.format,
            "time_pref": self.time_pref,
            "slot_id": self.slot_id,
            "pd_consent": bool(self.pd_consent),
            "active_booking_id": self.active_booking_id,
            "handoff_mode": bool(self.handoff_mode),
        }


def get_state(conversation: Conversation) -> ConversationState:
    """Return normalized conversation state.

    This function mirrors existing behavior of telegram_bot._get_state
    while adding explicit fields for active_booking_id and handoff_mode.
    """

    raw = conversation.state or {}
    state = ConversationState.from_raw(raw)
    conversation.state = state.to_dict()
    return state


def update_state(
    conversation: Conversation,
    updates: Dict[str, Any],
) -> ConversationState:
    """Merge updates into existing state and return the new value."""

    current = get_state(conversation)
    data = current.to_dict()
    data.update(updates)
    new_state = ConversationState.from_raw(data)
    conversation.state = new_state.to_dict()
    return new_state


def reset_flow(conversation: Conversation) -> ConversationState:
    """Reset flow-related fields while preserving pd_consent."""

    current = get_state(conversation)
    new_state = ConversationState(
        flow="other",
        step=0,
        pd_consent=current.pd_consent,
        goal=None,
        format=None,
        time_pref=None,
        slot_id=None,
        active_booking_id=None,
        handoff_mode=False,
    )
    conversation.state = new_state.to_dict()
    return new_state


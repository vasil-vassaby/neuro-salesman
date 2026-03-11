from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConversationState":
        """Create state instance from a plain dict."""

        return cls(
            flow=data.get("flow"),
            step=data.get("step"),
            pd_consent=bool(data.get("pd_consent", False)),
            active_booking_id=data.get("active_booking_id"),
            handoff_mode=bool(data.get("handoff_mode", False)),
            goal=data.get("goal"),
            format=data.get("format"),
            time_pref=data.get("time_pref"),
            slot_id=data.get("slot_id"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation of the state."""

        return {
            "flow": self.flow,
            "step": self.step,
            "pd_consent": self.pd_consent,
            "active_booking_id": self.active_booking_id,
            "handoff_mode": self.handoff_mode,
            "goal": self.goal,
            "format": self.format,
            "time_pref": self.time_pref,
            "slot_id": self.slot_id,
        }

    def merge_update(self, updates: Mapping[str, Any]) -> "ConversationState":
        """Return a new state with partial updates applied."""

        data = self.to_dict()
        data.update(updates)
        return ConversationState.from_dict(data)

    def reset_flow(self, preserve_consent: bool = True) -> "ConversationState":
        """Return a new state with dialog flow cleared.

        By default personal data consent and handoff flag are preserved.
        """

        pd_consent = self.pd_consent if preserve_consent else False
        return ConversationState(
            flow=None,
            step=None,
            pd_consent=pd_consent,
            active_booking_id=None,
            handoff_mode=self.handoff_mode,
            goal=None,
            format=None,
            time_pref=None,
            slot_id=None,
        )


__all__ = ["ConversationState"]


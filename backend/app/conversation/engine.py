from __future__ import annotations

from ..models import Conversation
from .state import ConversationState, get_state, reset_flow, update_state


def get_consent(conversation: Conversation) -> bool:
    """Return current personal data consent flag."""

    state: ConversationState = get_state(conversation)
    return bool(state.pd_consent)


def accept_consent(conversation: Conversation) -> ConversationState:
    """Mark personal data consent as accepted."""

    return update_state(conversation, {"pd_consent": True})


__all__ = [
    "ConversationState",
    "get_state",
    "reset_flow",
    "update_state",
    "get_consent",
    "accept_consent",
]


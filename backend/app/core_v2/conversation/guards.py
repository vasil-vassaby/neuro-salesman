from __future__ import annotations

from typing import Protocol

from .state import ConversationState


class Guard(Protocol):
    """Predicate that decides whether a transition is allowed."""

    def __call__(self, state: ConversationState) -> bool:
        ...


def has_consent(state: ConversationState) -> bool:
    """Return True when personal data consent is already recorded."""

    return bool(state.pd_consent)


__all__ = ["Guard", "has_consent"]


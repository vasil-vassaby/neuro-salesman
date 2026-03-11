from __future__ import annotations

from typing import Protocol

from .state import ConversationState


class Transition(Protocol):
    """Represents a pure state transition.

    Implementations take the current state and return the next state
    without performing side effects.
    """

    def __call__(self, state: ConversationState) -> ConversationState:
        ...


__all__ = ["Transition"]


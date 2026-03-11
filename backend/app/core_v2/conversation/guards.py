from __future__ import annotations

from typing import Protocol

from .state import ConversationState


class Guard(Protocol):
    """Predicate that decides whether a transition is allowed."""

    def __call__(self, state: ConversationState) -> bool:
        ...


__all__ = ["Guard"]


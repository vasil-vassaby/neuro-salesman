from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .state import ConversationState


@dataclass
class EngineInput:
    """Normalized input for the conversation engine."""

    text: Optional[str]
    payload: Optional[Dict[str, Any]]


@dataclass
class EngineResult:
    """Result of processing a single user input.

    This is a transport-agnostic representation of what should happen
    after the engine handles input.
    """

    state: ConversationState
    messages: list[str]


class ConversationEngine:
    """Core v2 conversation engine skeleton.

    The engine coordinates dialog state transitions and delegates
    business actions to services. Current implementation is only a
    typed contract without side effects.
    """

    def handle_input(
        self,
        state: ConversationState,
        engine_input: EngineInput,
    ) -> EngineResult:
        """Process user input and return new state and messages.

        This method must not perform real IO or database work in this
        skeleton version. Concrete implementations will be added later.
        """

        raise NotImplementedError


__all__ = ["ConversationEngine", "EngineInput", "EngineResult"]


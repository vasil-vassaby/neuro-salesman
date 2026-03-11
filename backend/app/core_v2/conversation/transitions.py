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


def start_flow(state: ConversationState) -> ConversationState:
    """Transition into consent flow after /start."""

    return state.merge_update(
        {
            "flow": "consent",
            "step": "ask_consent",
        }
    )


def consent_accepted(state: ConversationState) -> ConversationState:
    """Mark consent as accepted and keep flow for next step."""

    return state.merge_update(
        {
            "pd_consent": True,
        }
    )


def to_main_menu(state: ConversationState) -> ConversationState:
    """Transition to main menu, preserving consent."""

    base = state.reset_flow(preserve_consent=True)
    return base.merge_update(
        {
            "flow": "main_menu",
            "step": "idle",
        }
    )


def to_booking_flow(state: ConversationState) -> ConversationState:
    """Transition from main menu to booking flow."""

    return state.merge_update(
        {
            "flow": "booking",
            "step": "start",
        }
    )


def to_price_flow(state: ConversationState) -> ConversationState:
    """Transition from main menu to price/FAQ flow."""

    return state.merge_update(
        {
            "flow": "price",
            "step": "show_price",
        }
    )


def to_free_question_flow(state: ConversationState) -> ConversationState:
    """Transition from main menu to free question flow."""

    return state.merge_update(
        {
            "flow": "free_question",
            "step": "received",
        }
    )


__all__ = [
    "Transition",
    "start_flow",
    "consent_accepted",
    "to_main_menu",
    "to_booking_flow",
    "to_price_flow",
    "to_free_question_flow",
]


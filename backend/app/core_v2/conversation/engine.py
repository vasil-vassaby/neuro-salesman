from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..intents.detector import detect_intent
from ..intents.types import IntentType
from ..services.faq_service import ServiceAction, SimpleFaqService
from .guards import has_consent
from .state import ConversationState
from .transitions import (
    consent_accepted,
    start_flow,
    to_booking_flow,
    to_main_menu,
    to_price_flow,
    to_free_question_flow,
)


@dataclass
class EngineInput:
    """Normalized input for the conversation engine."""

    text: Optional[str]
    payload: Optional[Dict[str, Any]]


@dataclass
class EngineAction:
    """Transport-agnostic UI action offered to the user."""

    code: str
    label: str


@dataclass
class EngineMessage:
    """Transport-agnostic message produced by the engine."""

    text: str
    actions: List[EngineAction]


@dataclass
class EngineResult:
    """Result of processing a single user input.

    This is a transport-agnostic representation of what should happen
    after the engine handles input.
    """

    state: ConversationState
    messages: List[EngineMessage]


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

        This Core v2 mini-engine is fully in-memory and does not touch
        the database or external systems.
        """

        text = (engine_input.text or "").strip()
        intent = detect_intent(text, state_flow=state.flow)

        messages: List[EngineMessage] = []
        new_state = state
        faq_service = SimpleFaqService()

        if intent is IntentType.START:
            if has_consent(state):
                new_state = to_main_menu(state)
                messages.append(
                    EngineMessage(
                        text=(
                            "Главное меню. Вы можете записаться, узнать цену "
                            "или задать вопрос."
                        ),
                        actions=[],
                    )
                )
            else:
                new_state = start_flow(state)
                messages.append(
                    EngineMessage(
                        text="Здравствуйте! Я цифровой администратор эксперта.",
                        actions=[],
                    )
                )
                messages.append(
                    EngineMessage(
                        text=(
                            "Для продолжения нужна обработка персональных "
                            "данных. Если вы согласны, напишите «Согласен»."
                        ),
                        actions=[],
                    )
                )
        elif intent is IntentType.CONSENT_ACCEPT:
            new_state = consent_accepted(state)
            new_state = to_main_menu(new_state)
            messages.append(
                EngineMessage(
                    text="Спасибо, ваше согласие сохранено.",
                    actions=[],
                )
            )
            messages.append(
                EngineMessage(
                    text=(
                        "Главное меню. Вы можете записаться, узнать цену "
                        "или задать вопрос."
                    ),
                    actions=[],
                )
            )
        elif has_consent(state) and intent is IntentType.BOOKING:
            new_state = to_booking_flow(state)
            messages.append(
                EngineMessage(
                    text=(
                        "Вы выбрали запись на консультацию. "
                        "Скоро здесь появится сценарий выбора слота."
                    ),
                    actions=[],
                )
            )
        elif has_consent(state) and intent is IntentType.PRICE:
            new_state = to_price_flow(state)
            service_message = faq_service.get_price_info()
            actions = [
                EngineAction(code=a.code, label=a.label)
                for a in service_message.next_actions
            ]
            messages.append(
                EngineMessage(
                    text=service_message.text,
                    actions=actions,
                )
            )
        elif has_consent(state) and intent is IntentType.FREE_QUESTION:
            new_state = to_free_question_flow(state)
            messages.append(
                EngineMessage(
                    text=(
                        "Я зафиксировал ваш вопрос. В полной версии ядра "
                        "здесь будет сценарий обработки свободных вопросов."
                    ),
                    actions=[],
                )
            )
        else:
            messages.append(
                EngineMessage(
                    text=(
                        "Пока я понимаю только /start и сообщение "
                        "с подтверждением согласия."
                    ),
                    actions=[],
                )
            )

        return EngineResult(state=new_state, messages=messages)


__all__ = [
    "ConversationEngine",
    "EngineInput",
    "EngineAction",
    "EngineMessage",
    "EngineResult",
]


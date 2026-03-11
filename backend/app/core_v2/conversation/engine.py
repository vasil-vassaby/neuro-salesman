from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..intents.detector import detect_intent
from ..intents.types import IntentType
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
class EngineResult:
    """Result of processing a single user input.

    This is a transport-agnostic representation of what should happen
    after the engine handles input.

    TODO: later messages should become structured objects instead of
    raw strings to support buttons, formatting and channels.
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

        This Core v2 mini-engine is fully in-memory and does not touch
        the database or external systems.
        """

        text = (engine_input.text or "").strip()
        intent = detect_intent(text, state_flow=state.flow)

        messages: List[str] = []
        new_state = state

        if intent is IntentType.START:
            if has_consent(state):
                new_state = to_main_menu(state)
                messages.append(
                    "Главное меню. Вы можете записаться, узнать цену "
                    "или задать вопрос."
                )
            else:
                new_state = start_flow(state)
                messages.append(
                    "Здравствуйте! Я цифровой администратор эксперта."
                )
                messages.append(
                    "Для продолжения нужна обработка персональных "
                    "данных. Если вы согласны, напишите «Согласен»."
                )
        elif intent is IntentType.CONSENT_ACCEPT:
            new_state = consent_accepted(state)
            new_state = to_main_menu(new_state)
            messages.append("Спасибо, ваше согласие сохранено.")
            messages.append(
                "Главное меню. Вы можете записаться, узнать цену "
                "или задать вопрос."
            )
        elif has_consent(state) and intent is IntentType.BOOKING:
            new_state = to_booking_flow(state)
            messages.append(
                "Вы выбрали запись на консультацию. "
                "Скоро здесь появится сценарий выбора слота."
            )
        elif has_consent(state) and intent is IntentType.PRICE:
            new_state = to_price_flow(state)
            messages.append(
                "Здесь будет подробная информация о стоимости "
                "и форматах консультаций."
            )
        elif has_consent(state) and intent is IntentType.FREE_QUESTION:
            new_state = to_free_question_flow(state)
            messages.append(
                "Я зафиксировал ваш вопрос. В полной версии ядра "
                "здесь будет сценарий обработки свободных вопросов."
            )
        else:
            messages.append(
                "Пока я понимаю только /start и сообщение "
                "с подтверждением согласия."
            )

        return EngineResult(state=new_state, messages=messages)


__all__ = ["ConversationEngine", "EngineInput", "EngineResult"]


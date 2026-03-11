from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol


@dataclass
class ServiceAction:
    """Represents a possible next action after a service reply."""

    code: str
    label: str


@dataclass
class ServiceMessage:
    """Structured FAQ service response."""

    text: str
    next_actions: List[ServiceAction]


class FaqService(Protocol):
    """Interface for FAQ / price answers in Core v2."""

    def get_price_info(self) -> ServiceMessage:
        """Return structured answer for price intent."""

        raise NotImplementedError


class SimpleFaqService:
    """In-memory FAQ service for the first Core v2 iteration.

    TODO: later this service should read data from templates, KB and
    expert settings instead of hardcoded text.
    """

    def get_price_info(self) -> ServiceMessage:
        """Return a minimal Russian-language price explanation."""

        text = (
            "Стоимость консультации зависит от формата и длительности. "
            "Сейчас ядро находится в разработке, и здесь позже появится "
            "конкретное описание цен и пакетов."
        )

        next_actions = [
            ServiceAction(code="booking", label="Записаться на консультацию"),
            ServiceAction(code="ask_question", label="Задать уточняющий вопрос"),
        ]

        return ServiceMessage(text=text, next_actions=next_actions)


__all__ = ["ServiceAction", "ServiceMessage", "FaqService", "SimpleFaqService"]


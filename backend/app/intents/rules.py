from __future__ import annotations

from typing import Optional

from .types import IntentType


def classify_keywords(normalized: str) -> Optional[IntentType]:
    """Classify text by simple keyword rules without commands or state.

    This is a direct extraction of the existing rules_engine.detect_intent
    logic, but returns IntentType instead of raw strings.
    """

    if not normalized:
        return None

    if any(token in normalized for token in ["цена", "стоимость", "price"]):
        return IntentType.price

    if any(
        token in normalized
        for token in [
            "записаться",
            "запись",
            "хочу записаться",
            "appointment",
            "book",
        ]
    ):
        return IntentType.booking

    if any(
        token in normalized
        for token in [
            "как проходит",
            "как пройдет",
            "как пройдёт",
            "что будет на приеме",
            "что будет на приёме",
            "how it works",
        ]
    ):
        return IntentType.how_it_works

    if any(
        token in normalized
        for token in [
            "сколько длится",
            "длительность",
            "duration",
        ]
    ):
        return IntentType.duration

    if any(
        token in normalized
        for token in [
            "где принимаете",
            "где вы находитесь",
            "адрес",
            "куда идти",
            "address",
            "location",
        ]
    ):
        return IntentType.location

    if any(
        token in normalized
        for token in [
            "что взять",
            "как подготовиться",
            "как подготовится",
            "prepare",
            "preparation",
        ]
    ):
        return IntentType.preparation

    if any(
        token in normalized
        for token in [
            "противопоказания",
            "можно ли при",
            "contraindications",
        ]
    ):
        return IntentType.contraindications

    if any(
        token in normalized
        for token in [
            "перенести",
            "перенос",
            "другое время",
            "reschedule",
        ]
    ):
        return IntentType.reschedule

    if any(
        token in normalized
        for token in ["услуги", "что делаете", "services"]
    ):
        return IntentType.services

    if any(
        token in normalized
        for token in ["дорого", "слишком дорого", "expensive"]
    ):
        return IntentType.objection_price

    if any(
        token in normalized
        for token in ["сомневаюсь", "не уверен", "doubt"]
    ):
        return IntentType.doubt

    return None


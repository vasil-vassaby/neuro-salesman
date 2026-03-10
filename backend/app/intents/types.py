from __future__ import annotations

from enum import Enum


class IntentType(str, Enum):
    start = "start"
    help = "help"
    reset = "reset"
    booking = "booking"
    price = "price"
    faq = "faq"
    handoff = "handoff"
    free_question = "free_question"
    other = "other"

    # существующие детализированные intents из rules_engine
    how_it_works = "how_it_works"
    duration = "duration"
    location = "location"
    preparation = "preparation"
    contraindications = "contraindications"
    reschedule = "reschedule"
    services = "services"
    objection_price = "objection_price"
    doubt = "doubt"


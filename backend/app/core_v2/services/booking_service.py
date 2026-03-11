from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol


@dataclass
class AvailableSlotDTO:
    """Lightweight view of an available slot."""

    id: str
    starts_at_utc: datetime
    ends_at_utc: datetime
    capacity: int
    reserved_count: int


@dataclass
class BookingDTO:
    """Lightweight view of a booking."""

    id: str
    lead_id: str
    slot_id: str
    offer_id: Optional[str]
    status: str
    source: str


@dataclass
class BookingServiceAction:
    """Represents a suggested next action in booking flow."""

    code: str
    label: str


@dataclass
class BookingServiceMessage:
    """Structured response from booking service."""

    text: str
    next_actions: List[BookingServiceAction]


class BookingService(Protocol):
    """Interface for booking-related operations in Core v2.

    For now it exposes only booking entry for Core v2 prototype.
    """

    def get_booking_entry(self) -> BookingServiceMessage:
        """Return structured response for the start of booking flow."""

        raise NotImplementedError


class SimpleBookingService:
    """In-memory booking service for the first Core v2 iteration.

    TODO: later this service should use real slots, offers and
    expert settings to drive the booking flow.
    """

    def get_booking_entry(self) -> BookingServiceMessage:
        """Return a minimal Russian-language booking entry message."""

        text = (
            "Вы начали сценарий записи на консультацию. "
            "Далее нужно выбрать цель, формат и удобное время."
        )
        next_actions = [
            BookingServiceAction(code="choose_goal", label="Выбрать цель"),
            BookingServiceAction(code="choose_format", label="Выбрать формат"),
            BookingServiceAction(code="choose_time", label="Выбрать удобное время"),
        ]
        return BookingServiceMessage(text=text, next_actions=next_actions)


__all__ = [
    "AvailableSlotDTO",
    "BookingDTO",
    "BookingServiceAction",
    "BookingServiceMessage",
    "BookingService",
    "SimpleBookingService",
]


from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol


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


class BookingService(Protocol):
    """Interface for booking-related operations in Core v2.

    Implementations must be transactional and enforce booking
    invariants but the skeleton does not perform real database work.
    """

    def get_top_slots(
        self,
        time_pref: Optional[str],
        limit: int = 3,
    ) -> list[AvailableSlotDTO]:
        """Return a small list of upcoming available slots."""

        raise NotImplementedError

    def create_booking_with_reminders(
        self,
        *,
        lead_id: str,
        slot_id: str,
        offer_id: Optional[str],
        source: str,
        contact_name: str,
        contact_phone: str,
        contact_message: Optional[str],
    ) -> BookingDTO:
        """Create booking and schedule reminders.

        Real implementations must:
        - check slot capacity
        - create booking transactionally
        - schedule reminders only after booking id exists
        """

        raise NotImplementedError


__all__ = ["AvailableSlotDTO", "BookingDTO", "BookingService"]


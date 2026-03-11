from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class ReminderDTO:
    """Lightweight reminder representation for Core v2."""

    id: str
    booking_id: str
    remind_at_utc: datetime
    channel: str
    status: str


class ReminderService(Protocol):
    """Interface for reminder management in Core v2."""

    def recreate_for_booking(self, booking_id: str) -> list[ReminderDTO]:
        """Recreate reminders for a booking.

        Implementations must:
        - cancel previous pending reminders
        - schedule new reminders in UTC
        """

        raise NotImplementedError


__all__ = ["ReminderDTO", "ReminderService"]


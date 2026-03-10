from __future__ import annotations

from datetime import timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from ..config import settings
from ..models import (
    AvailableSlot,
    Booking,
    EventLog,
    ReminderQueueItem,
)
from ..utils.timezone import now_utc


def get_top_slots(session: Session, time_pref: Optional[str]) -> List[AvailableSlot]:
    """Return up to 3 upcoming available slots filtered by time preference."""

    now = now_utc()
    query = (
        session.query(AvailableSlot)
        .filter(
            AvailableSlot.is_active.is_(True),
            AvailableSlot.reserved_count < AvailableSlot.capacity,
            AvailableSlot.starts_at > now,
        )
        .order_by(AvailableSlot.starts_at.asc())
    )
    candidates = query.limit(50).all()
    result: List[AvailableSlot] = []
    for slot in candidates:
        local_hour = slot.starts_at.astimezone(settings.tzinfo).hour
        if time_pref == "day":
            if (
                local_hour >= settings.day_start_hour
                and local_hour < settings.day_end_hour
            ):
                result.append(slot)
        elif time_pref == "evening":
            if local_hour >= settings.day_end_hour:
                result.append(slot)
        else:
            result.append(slot)
        if len(result) >= 3:
            break
    return result


def get_reschedule_slots(
    session: Session,
    current_slot: AvailableSlot,
    limit: int = 3,
) -> List[AvailableSlot]:
    """Return alternative available slots for reschedule."""

    now = now_utc()
    query = (
        session.query(AvailableSlot)
        .filter(
            AvailableSlot.is_active.is_(True),
            AvailableSlot.reserved_count < AvailableSlot.capacity,
            AvailableSlot.starts_at > now,
            AvailableSlot.id != current_slot.id,
        )
        .order_by(AvailableSlot.starts_at.asc())
    )
    return query.limit(limit).all()


def _schedule_reminders(
    session: Session,
    booking: Booking,
) -> None:
    scheduled_at = booking.scheduled_at
    if (
        not settings.reminder_enabled
        or scheduled_at is None
        or not booking.id
    ):
        return
    for hours_before in (
        settings.reminder_1_hours_before,
        settings.reminder_2_hours_before,
    ):
        if hours_before <= 0:
            continue
        remind_at = scheduled_at - timedelta(hours=hours_before)
        if remind_at <= now_utc():
            continue
        reminder = ReminderQueueItem(
            booking_id=booking.id,
            remind_at=remind_at,
        )
        session.add(reminder)


def create_booking_with_reminders(
    session: Session,
    *,
    lead_id: UUID,
    slot: AvailableSlot,
    offer_id: Optional[UUID],
    source: str,
    contact_name: str,
    contact_phone: str,
    contact_message: Optional[str],
) -> Booking:
    """Create booking transactionally, increment slot and schedule reminders."""

    if slot.reserved_count >= slot.capacity:
        raise ValueError("slot_capacity_exceeded")

    slot.reserved_count += 1

    booking = Booking(
        lead_id=lead_id,
        offer_id=offer_id,
        slot_id=slot.id,
        status="requested",
        scheduled_at=slot.starts_at,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_message=contact_message,
        source=source,
    )
    session.add(booking)
    session.flush()

    event = EventLog(
        event_type="booking_created",
        payload={
            "booking_id": str(booking.id),
            "lead_id": str(lead_id),
            "slot_id": str(slot.id),
            "source": source,
        },
    )
    session.add(event)

    _schedule_reminders(session, booking)

    return booking


def cancel_booking_slot_reservation(session: Session, booking: Booking) -> None:
    """Free reserved slot capacity when booking is cancelled."""

    if booking.slot_id is None:
        return
    slot = (
        session.query(AvailableSlot)
        .with_for_update()
        .filter(AvailableSlot.id == booking.slot_id)
        .first()
    )
    if slot is not None and slot.reserved_count > 0:
        slot.reserved_count -= 1


def reschedule_booking_with_reminders(
    session: Session,
    booking: Booking,
    current_slot: Optional[AvailableSlot],
    new_slot: AvailableSlot,
) -> Tuple[int, int]:
    """Move booking to new slot, update counters and recreate reminders.

    Returns:
        tuple (released_count, created_reminders)
    """

    now = now_utc()
    if new_slot.starts_at <= now:
        raise ValueError("new_slot_in_past")

    released = 0
    if current_slot is not None and current_slot.reserved_count > 0:
        current_slot.reserved_count -= 1
        released = 1

    new_slot.reserved_count += 1

    booking.slot_id = new_slot.id
    booking.scheduled_at = new_slot.starts_at

    cancelled_items = (
        session.query(ReminderQueueItem)
        .with_for_update()
        .filter(
            ReminderQueueItem.booking_id == booking.id,
            ReminderQueueItem.status == "pending",
        )
        .all()
    )
    for item in cancelled_items:
        item.status = "cancelled"
        item.last_error = "rescheduled"

    created = 0
    if settings.reminder_enabled and booking.scheduled_at is not None:
        for hours_before in (
            settings.reminder_1_hours_before,
            settings.reminder_2_hours_before,
        ):
            if hours_before <= 0:
                continue
            remind_at = booking.scheduled_at - timedelta(hours=hours_before)
            if remind_at <= now_utc():
                continue
            reminder = ReminderQueueItem(
                booking_id=booking.id,
                remind_at=remind_at,
            )
            session.add(reminder)
            created += 1

    return released, created


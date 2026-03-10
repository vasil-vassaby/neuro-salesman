from datetime import timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..db import SessionLocal
from ..models import (
    AvailableSlot,
    Booking,
    Conversation,
    EventLog,
    Lead,
    Message,
    ReminderQueueItem,
)
from ..schemas import BookingOut, WebBookingRequest, WebLeadRequest
from ..utils.timezone import format_local_datetime, now_utc


router = APIRouter(prefix="/api")


def _get_db_session() -> Session:
    return SessionLocal()


@router.post("/web/leads")
def create_web_lead(payload: WebLeadRequest) -> dict:
    session = _get_db_session()
    try:
        lead = Lead(
            display_name=payload.name,
            phone=payload.phone,
            status="new",
        )
        session.add(lead)
        session.flush()
        conversation = Conversation(
            lead_id=lead.id,
            channel="web",
        )
        session.add(conversation)
        session.flush()
        message = Message(
            conversation_id=conversation.id,
            lead_id=lead.id,
            channel="web",
            direction="inbound",
            text=payload.message,
            delivery_status="sent",
        )
        session.add(message)
        session.commit()
        return {
            "ok": True,
            "lead_id": str(lead.id),
            "conversation_id": str(conversation.id),
        }
    finally:
        session.close()


@router.post("/web/bookings")
def create_web_booking(payload: WebBookingRequest) -> dict:
    session = _get_db_session()
    try:
        slot = (
            session.query(AvailableSlot)
            .with_for_update()
            .filter(
                AvailableSlot.id == payload.slot_id,
                AvailableSlot.is_active.is_(True),
            )
            .first()
        )
        if slot is None:
            raise HTTPException(status_code=404, detail="Слот не найден.")
        if slot.reserved_count >= slot.capacity:
            raise HTTPException(
                status_code=409,
                detail="Слот уже занят, выберите другое время.",
            )
        slot.reserved_count += 1

        lead = Lead(
            display_name=payload.name,
            phone=payload.phone,
            status="new",
        )
        session.add(lead)
        session.flush()

        conversation = Conversation(
            lead_id=lead.id,
            channel="web",
        )
        session.add(conversation)
        session.flush()

        message = Message(
            conversation_id=conversation.id,
            lead_id=lead.id,
            channel="web",
            direction="inbound",
            text=payload.message,
            delivery_status="sent",
        )
        session.add(message)

        scheduled_at = slot.starts_at
        booking = Booking(
            lead_id=lead.id,
            offer_id=payload.offer_id,
            slot_id=slot.id,
            status="requested",
            scheduled_at=scheduled_at,
            contact_name=payload.name,
            contact_phone=payload.phone,
            contact_message=payload.message,
            source="web",
        )
        session.add(booking)
        session.flush()

        event = EventLog(
            event_type="booking_created",
            payload={
                "booking_id": str(booking.id),
                "lead_id": str(lead.id),
                "slot_id": str(slot.id),
                "source": "web",
            },
        )
        session.add(event)

        if settings.reminder_enabled and scheduled_at is not None:
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

        session.commit()
        confirmation_time = format_local_datetime(scheduled_at)
        confirmation_text = (
            f"Запись принята на {confirmation_time}. "
            "Мы дополнительно подтвердим время."
        )
        return {
            "ok": True,
            "booking": BookingOut.from_orm(booking),
            "message": confirmation_text,
        }
    except HTTPException:
        session.rollback()
        raise
    finally:
        session.close()


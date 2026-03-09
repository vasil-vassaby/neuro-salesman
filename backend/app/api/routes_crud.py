import asyncio
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..db import SessionLocal
from ..models import (
    AvailableSlot,
    Booking,
    Conversation,
    EventLog,
    KbArticle,
    Lead,
    LeadStatusHistory,
    LostReason,
    Message,
    Offer,
    ReplyTemplate,
)
from ..reminders import CONFIRM_TEXT_TEMPLATE, _format_dt, _send_telegram_message
from ..schemas import (
    AvailableSlotCreate,
    AvailableSlotOut,
    AvailableSlotUpdate,
    BookingOut,
    BookingStatusUpdate,
    KbArticleCreate,
    KbArticleOut,
    KbArticleUpdate,
    LeadLostRequest,
    OfferCreate,
    OfferOut,
    OfferUpdate,
    ReplyTemplateCreate,
    ReplyTemplateOut,
    ReplyTemplateUpdate,
)


router = APIRouter(prefix="/api")


def _get_db_session() -> Session:
    return SessionLocal()


# KB Articles CRUD


@router.get("/kb_articles", response_model=List[KbArticleOut])
def list_kb_articles() -> List[KbArticleOut]:
    session = _get_db_session()
    try:
        articles = session.query(KbArticle).all()
        return [KbArticleOut.from_orm(article) for article in articles]
    finally:
        session.close()


@router.post("/kb_articles", response_model=KbArticleOut)
def create_kb_article(payload: KbArticleCreate) -> KbArticleOut:
    session = _get_db_session()
    try:
        article = KbArticle(
            external_id=payload.external_id,
            title=payload.title,
            category=payload.category,
            content=payload.content,
            active=payload.active,
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        return KbArticleOut.from_orm(article)
    finally:
        session.close()


@router.get("/kb_articles/{article_id}", response_model=KbArticleOut)
def get_kb_article(article_id: str) -> KbArticleOut:
    session = _get_db_session()
    try:
        article = session.get(KbArticle, UUID(article_id))
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        return KbArticleOut.from_orm(article)
    finally:
        session.close()


@router.put("/kb_articles/{article_id}", response_model=KbArticleOut)
def update_kb_article(
    article_id: str,
    payload: KbArticleUpdate,
) -> KbArticleOut:
    session = _get_db_session()
    try:
        article = session.get(KbArticle, UUID(article_id))
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(article, field, value)
        session.commit()
        session.refresh(article)
        return KbArticleOut.from_orm(article)
    finally:
        session.close()


@router.delete("/kb_articles/{article_id}")
def delete_kb_article(article_id: str) -> dict:
    session = _get_db_session()
    try:
        article = session.get(KbArticle, UUID(article_id))
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        session.delete(article)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


# Offers CRUD


@router.get("/offers", response_model=List[OfferOut])
def list_offers() -> List[OfferOut]:
    session = _get_db_session()
    try:
        offers = session.query(Offer).all()
        return [OfferOut.from_orm(offer) for offer in offers]
    finally:
        session.close()


@router.post("/offers", response_model=OfferOut)
def create_offer(payload: OfferCreate) -> OfferOut:
    session = _get_db_session()
    try:
        offer = Offer(**payload.dict())
        session.add(offer)
        session.commit()
        session.refresh(offer)
        return OfferOut.from_orm(offer)
    finally:
        session.close()


@router.get("/offers/{offer_id}", response_model=OfferOut)
def get_offer(offer_id: str) -> OfferOut:
    session = _get_db_session()
    try:
        offer = session.get(Offer, UUID(offer_id))
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        return OfferOut.from_orm(offer)
    finally:
        session.close()


@router.put("/offers/{offer_id}", response_model=OfferOut)
def update_offer(
    offer_id: str,
    payload: OfferUpdate,
) -> OfferOut:
    session = _get_db_session()
    try:
        offer = session.get(Offer, UUID(offer_id))
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(offer, field, value)
        session.commit()
        session.refresh(offer)
        return OfferOut.from_orm(offer)
    finally:
        session.close()


@router.delete("/offers/{offer_id}")
def delete_offer(offer_id: str) -> dict:
    session = _get_db_session()
    try:
        offer = session.get(Offer, UUID(offer_id))
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        session.delete(offer)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


# Reply templates CRUD


@router.get("/reply_templates", response_model=List[ReplyTemplateOut])
def list_reply_templates() -> List[ReplyTemplateOut]:
    session = _get_db_session()
    try:
        templates = session.query(ReplyTemplate).all()
        return [ReplyTemplateOut.from_orm(tpl) for tpl in templates]
    finally:
        session.close()


@router.post("/reply_templates", response_model=ReplyTemplateOut)
def create_reply_template(payload: ReplyTemplateCreate) -> ReplyTemplateOut:
    session = _get_db_session()
    try:
        template = ReplyTemplate(**payload.dict())
        session.add(template)
        session.commit()
        session.refresh(template)
        return ReplyTemplateOut.from_orm(template)
    finally:
        session.close()


@router.get("/reply_templates/{template_id}", response_model=ReplyTemplateOut)
def get_reply_template(template_id: str) -> ReplyTemplateOut:
    session = _get_db_session()
    try:
        template = session.get(ReplyTemplate, UUID(template_id))
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        return ReplyTemplateOut.from_orm(template)
    finally:
        session.close()


@router.put("/reply_templates/{template_id}", response_model=ReplyTemplateOut)
def update_reply_template(
    template_id: str,
    payload: ReplyTemplateUpdate,
) -> ReplyTemplateOut:
    session = _get_db_session()
    try:
        template = session.get(ReplyTemplate, UUID(template_id))
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        session.commit()
        session.refresh(template)
        return ReplyTemplateOut.from_orm(template)
    finally:
        session.close()


@router.delete("/reply_templates/{template_id}")
def delete_reply_template(template_id: str) -> dict:
    session = _get_db_session()
    try:
        template = session.get(ReplyTemplate, UUID(template_id))
        if template is None:
            raise HTTPException(status_code=404, detail="Template not found")
        session.delete(template)
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@router.get("/lost_reasons")
def list_lost_reasons() -> List[dict]:
    session = _get_db_session()
    try:
        reasons = session.query(LostReason).filter(LostReason.active.is_(True)).all()
        return [
            {
                "code": reason.code,
                "title": reason.title,
                "description": reason.description,
            }
            for reason in reasons
        ]
    finally:
        session.close()


@router.get("/slots", response_model=List[AvailableSlotOut])
def list_slots(
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> List[AvailableSlotOut]:
    session = _get_db_session()
    try:
        query = session.query(AvailableSlot).filter(
            AvailableSlot.is_active.is_(True),
        )
        if from_dt is not None:
            query = query.filter(AvailableSlot.starts_at >= from_dt)
        if to_dt is not None:
            query = query.filter(AvailableSlot.starts_at <= to_dt)
        slots = query.order_by(AvailableSlot.starts_at.asc()).all()
        return [AvailableSlotOut.from_orm(slot) for slot in slots]
    finally:
        session.close()


@router.post("/slots", response_model=AvailableSlotOut)
def create_slot(payload: AvailableSlotCreate) -> AvailableSlotOut:
    session = _get_db_session()
    try:
        slot = AvailableSlot(
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            capacity=payload.capacity,
            notes=payload.notes,
        )
        session.add(slot)
        session.commit()
        session.refresh(slot)
        return AvailableSlotOut.from_orm(slot)
    finally:
        session.close()


@router.patch("/slots/{slot_id}", response_model=AvailableSlotOut)
def update_slot(slot_id: str, payload: AvailableSlotUpdate) -> AvailableSlotOut:
    session = _get_db_session()
    try:
        slot = session.get(AvailableSlot, UUID(slot_id))
        if slot is None:
            raise HTTPException(status_code=404, detail="Slot not found")
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(slot, field, value)
        session.commit()
        session.refresh(slot)
        return AvailableSlotOut.from_orm(slot)
    finally:
        session.close()


@router.delete("/slots/{slot_id}")
def deactivate_slot(slot_id: str) -> dict:
    session = _get_db_session()
    try:
        slot = session.get(AvailableSlot, UUID(slot_id))
        if slot is None:
            raise HTTPException(status_code=404, detail="Slot not found")
        slot.is_active = False
        session.commit()
        return {"ok": True}
    finally:
        session.close()


@router.get("/bookings", response_model=List[BookingOut])
def list_bookings(
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    lead_id: Optional[str] = None,
) -> List[BookingOut]:
    session = _get_db_session()
    try:
        query = session.query(Booking)
        if lead_id is not None:
            query = query.filter(Booking.lead_id == UUID(lead_id))
        if from_dt is not None:
            query = query.filter(Booking.scheduled_at >= from_dt)
        if to_dt is not None:
            query = query.filter(Booking.scheduled_at <= to_dt)
        bookings = query.order_by(Booking.scheduled_at.asc()).all()
        return [BookingOut.from_orm(booking) for booking in bookings]
    finally:
        session.close()


@router.patch("/bookings/{booking_id}", response_model=BookingOut)
def update_booking_status(
    booking_id: str,
    payload: BookingStatusUpdate,
) -> BookingOut:
    allowed_statuses = {"requested", "confirmed", "cancelled", "no_show"}
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid booking status")

    session = _get_db_session()
    booking_data: Optional[BookingOut] = None
    need_confirm = False
    lead_id: Optional[UUID] = None
    try:
        booking = session.get(Booking, UUID(booking_id))
        if booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        old_status = booking.status
        new_status = payload.status

        if old_status == "requested" and new_status not in {
            "confirmed",
            "cancelled",
        }:
            raise HTTPException(status_code=400, detail="Invalid status transition")
        if old_status == "confirmed" and new_status not in {
            "cancelled",
            "no_show",
        }:
            raise HTTPException(status_code=400, detail="Invalid status transition")
        if old_status in {"cancelled", "no_show"} and new_status != old_status:
            raise HTTPException(status_code=400, detail="Cannot change final status")

        if (
            new_status == "cancelled"
            and booking.slot_id is not None
            and old_status in {"requested", "confirmed"}
        ):
            slot = (
                session.query(AvailableSlot)
                .with_for_update()
                .filter(AvailableSlot.id == booking.slot_id)
                .first()
            )
            if slot is not None and slot.reserved_count > 0:
                slot.reserved_count -= 1

        booking.status = new_status
        booking.cancel_reason = payload.cancel_reason

        event = EventLog(
            event_type="booking_status_changed",
            payload={
                "booking_id": str(booking.id),
                "from": old_status,
                "to": new_status,
            },
        )
        session.add(event)

        if new_status in {"confirmed", "cancelled", "no_show"}:
            conversation = (
                session.query(Conversation)
                .filter(
                    Conversation.lead_id == booking.lead_id,
                    Conversation.channel == "telegram",
                )
                .first()
            )
            if conversation is not None:
                before_state = conversation.state
                conversation.state = {}
                reset_event = EventLog(
                    event_type="conversation_state_reset",
                    payload={
                        "conversation_id": str(conversation.id),
                        "lead_id": str(booking.lead_id),
                        "reason": f"booking_{new_status}",
                        "before_state": before_state,
                    },
                )
                session.add(reset_event)

        session.commit()
        session.refresh(booking)
        booking_data = BookingOut.from_orm(booking)
        if new_status == "confirmed":
            need_confirm = True
            lead_id = booking.lead_id
    finally:
        session.close()

    if need_confirm and lead_id is not None:
        session = _get_db_session()
        try:
            conversation = (
                session.query(Conversation)
                .filter(
                    Conversation.lead_id == lead_id,
                    Conversation.channel == "telegram",
                )
                .first()
            )
            chat_id = (
                str(conversation.external_chat_id)
                if conversation and conversation.external_chat_id
                else None
            )
            if chat_id and settings.telegram_bot_token:
                text = CONFIRM_TEXT_TEMPLATE.format(
                    date_time=_format_dt(booking_data.scheduled_at),
                )
                outbound = Message(
                    conversation_id=conversation.id,
                    lead_id=lead_id,
                    channel="telegram",
                    direction="outbound",
                    text=text,
                    delivery_status="unknown",
                )
                session.add(outbound)
                session.flush()

                status, error = asyncio.run(
                    _send_telegram_message(chat_id=chat_id, text=text),
                )
                stored = session.get(Message, outbound.id)
                if stored is not None:
                    stored.delivery_status = status
                    stored.delivery_error = error

                confirm_event = EventLog(
                    event_type="booking_confirm_notification",
                    payload={
                        "booking_id": str(booking_data.id),
                        "lead_id": str(lead_id),
                        "delivery_status": status,
                    },
                )
                session.add(confirm_event)
                session.commit()
            else:
                no_chat_event = EventLog(
                    event_type="booking_confirm_notification_skipped",
                    payload={
                        "booking_id": str(booking_data.id),
                        "lead_id": str(lead_id),
                        "reason": "no_telegram_channel",
                    },
                )
                session.add(no_chat_event)
                session.commit()
        finally:
            session.close()

    return booking_data


@router.get("/leads/{lead_id}/bookings", response_model=List[BookingOut])
def list_lead_bookings(lead_id: str) -> List[BookingOut]:
    session = _get_db_session()
    try:
        bookings = (
            session.query(Booking)
            .filter(Booking.lead_id == UUID(lead_id))
            .order_by(Booking.created_at.asc())
            .all()
        )
        return [BookingOut.from_orm(booking) for booking in bookings]
    finally:
        session.close()


@router.post("/leads/{lead_id}/lost")
def mark_lead_lost(lead_id: str, payload: LeadLostRequest) -> dict:
    session = _get_db_session()
    try:
        lead = session.get(Lead, UUID(lead_id))
        if lead is None:
            raise HTTPException(status_code=404, detail="Lead not found")

        reason = (
            session.query(LostReason)
            .filter(LostReason.code == payload.reason_code)
            .first()
        )
        if reason is None:
            raise HTTPException(status_code=400, detail="Unknown reason code")

        previous_status = lead.status
        lead.status = "lost"

        history = LeadStatusHistory(
            lead_id=lead.id,
            from_status=previous_status,
            to_status="lost",
            reason=payload.note,
            reason_code=payload.reason_code,
        )
        session.add(history)

        event = EventLog(
            event_type="lead_lost",
            payload={
                "lead_id": str(lead.id),
                "from_status": previous_status,
                "reason_code": payload.reason_code,
            },
        )
        session.add(event)

        session.commit()
        return {"ok": True}
    finally:
        session.close()


import asyncio
from typing import List

from fastapi import APIRouter, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..config import settings
from ..db import SessionLocal
from ..models import Conversation, Lead, Message
from ..schemas import (
    ConversationDetail,
    ConversationSummary,
    LeadSummary,
    MessageBase,
    SendMessageRequest,
)
from ..telegram_bot import TelegramClient


router = APIRouter(prefix="/api")


def _get_db_session() -> Session:
    return SessionLocal()


@router.get("/inbox/conversations", response_model=List[ConversationSummary])
def list_conversations() -> List[ConversationSummary]:
    session = _get_db_session()
    try:
        conversations = (
            session.query(Conversation)
            .order_by(desc(Conversation.last_inbound_at))
            .limit(100)
            .all()
        )
        results: List[ConversationSummary] = []
        for conv in conversations:
            lead = conv.lead
            last_message = (
                session.query(Message)
                .filter(Message.conversation_id == conv.id)
                .order_by(desc(Message.created_at))
                .first()
            )
            summary = ConversationSummary(
                id=conv.id,
                lead=LeadSummary(
                    id=lead.id,
                    display_name=lead.display_name,
                    status=lead.status,
                ),
                channel=conv.channel,
                last_message_text=last_message.text if last_message else None,
                last_message_at=last_message.created_at if last_message else None,
            )
            results.append(summary)
        return results
    finally:
        session.close()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str) -> ConversationDetail:
    session = _get_db_session()
    try:
        conversation = (
            session.query(Conversation).filter(Conversation.id == conversation_id).first()
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        lead = conversation.lead
        messages = (
            session.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        return ConversationDetail(
            id=conversation.id,
            lead=LeadSummary(
                id=lead.id,
                display_name=lead.display_name,
                status=lead.status,
            ),
            channel=conversation.channel,
            state=conversation.state or {},
            messages=[
                MessageBase(
                    id=msg.id,
                    direction=msg.direction,
                    text=msg.text,
                    created_at=msg.created_at,
                    delivery_status=msg.delivery_status,
                    delivery_error=msg.delivery_error,
                )
                for msg in messages
            ],
        )
    finally:
        session.close()


@router.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: str, payload: SendMessageRequest) -> dict:
    session = _get_db_session()
    try:
        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        lead = conversation.lead
        channel = conversation.channel
        external_chat_id = conversation.external_chat_id
        message = Message(
            conversation_id=conversation.id,
            lead_id=lead.id,
            channel=channel,
            direction="outbound",
            text=payload.text,
            delivery_status="unknown",
        )
        session.add(message)
        session.commit()
        session.refresh(message)
    finally:
        session.close()

    delivery_status = "failed"
    delivery_error = None
    if channel == "telegram" and settings.telegram_bot_token and external_chat_id:
        client = TelegramClient(settings.telegram_bot_token)

        async def _send() -> None:
            nonlocal delivery_status, delivery_error
            try:
                response = await client.send_message(
                    chat_id=str(external_chat_id),
                    text=payload.text,
                )
                if response.get("ok"):
                    delivery_status = "sent"
                else:
                    delivery_error = str(response)
            except Exception as exc:
                delivery_error = str(exc)

        asyncio.run(_send())
    else:
        delivery_status = "sent"

    session = _get_db_session()
    try:
        stored = session.get(Message, message.id)
        if stored is not None:
            stored.delivery_status = delivery_status
            stored.delivery_error = delivery_error
            session.commit()
    finally:
        session.close()

    return {"ok": True, "delivery_status": delivery_status}



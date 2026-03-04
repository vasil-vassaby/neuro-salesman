from fastapi import APIRouter
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import Conversation, Lead, Message
from ..schemas import WebLeadRequest


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
        return {"ok": True, "lead_id": str(lead.id), "conversation_id": str(conversation.id)}
    finally:
        session.close()


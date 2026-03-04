import logging
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from .config import settings
from .models import ReplyTemplate


logger = logging.getLogger(__name__)


def detect_intent(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["цена", "стоимост", "price"]):
        return "price"
    if any(token in lowered for token in ["записаться", "записать", "appointment", "book"]):
        return "booking"
    if any(token in lowered for token in ["адрес", "где вы", "куда идти", "address"]):
        return "address"
    if any(token in lowered for token in ["услуги", "что делаете", "services"]):
        return "services"
    if any(token in lowered for token in ["дорого", "слишком дорого", "expensive"]):
        return "objection_price"
    if any(token in lowered for token in ["сомневаюсь", "не уверен", "doubt"]):
        return "doubt"
    if any(token in lowered for token in ["противопоказания", "contraindications"]):
        return "contraindications"
    return "other"


def _select_template_query(intent: str, channel: str) -> select:
    query = select(ReplyTemplate).where(
        and_(
            ReplyTemplate.intent == intent,
            ReplyTemplate.active.is_(True),
        ),
    )
    channel_filter = or_(
        ReplyTemplate.channel.is_(None),
        ReplyTemplate.channel == channel,
    )
    query = query.where(channel_filter)
    return query


def choose_reply_template(
    session: Session,
    intent: str,
    channel: str,
) -> Optional[ReplyTemplate]:
    query = _select_template_query(intent, channel)
    template = session.execute(query).scalars().first()
    if template:
        return template
    fallback = session.execute(
        select(ReplyTemplate).where(
            and_(
                ReplyTemplate.key == "fallback_web",
                ReplyTemplate.active.is_(True),
            ),
        ),
    ).scalar_one_or_none()
    if fallback is None:
        logger.warning("Fallback template 'fallback_web' not found.")
    return fallback


def render_template_text(template: ReplyTemplate) -> str:
    web_url = settings.web_url
    text = template.text.replace("{web_url}", web_url)
    return text


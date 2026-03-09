import logging
from typing import Mapping, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from .config import settings
from .models import ReplyTemplate


logger = logging.getLogger(__name__)


_FLOW_STEP_KEY_MAP: dict[tuple[str, int], str] = {
    ("booking", 1): "booking_step_goal",
    ("booking", 2): "booking_step_format",
    ("booking", 3): "booking_step_time",
    ("booking", 4): "booking_step_slots",
    ("booking", 5): "booking_confirm_requested",
    ("price", 1): "price_step_goal",
    ("reschedule", 1): "booking_reschedule_intro",
    ("reschedule", 2): "booking_reschedule_slots",
    ("reschedule", 3): "booking_reschedule_confirm",
}


def detect_intent(text: str) -> str:
    normalized = (text or "").strip().casefold()
    if not normalized:
        return "other"
    if any(token in normalized for token in ["цена", "стоимость", "price"]):
        return "price"
    if any(
        token in normalized
        for token in [
            "записаться",
            "запись",
            "хочу записаться",
            "appointment",
            "book",
        ]
    ):
        return "booking"
    if any(
        token in normalized
        for token in [
            "как проходит",
            "как пройдет",
            "как пройдёт",
            "что будет на приеме",
            "что будет на приёме",
            "how it works",
        ]
    ):
        return "how_it_works"
    if any(
        token in normalized
        for token in [
            "сколько длится",
            "длительность",
            "duration",
        ]
    ):
        return "duration"
    if any(
        token in normalized
        for token in [
            "где принимаете",
            "где вы находитесь",
            "адрес",
            "куда идти",
            "address",
            "location",
        ]
    ):
        return "location"
    if any(
        token in normalized
        for token in [
            "что взять",
            "как подготовиться",
            "как подготовится",
            "prepare",
            "preparation",
        ]
    ):
        return "preparation"
    if any(
        token in normalized
        for token in [
            "противопоказания",
            "можно ли при",
            "contraindications",
        ]
    ):
        return "contraindications"
    if any(
        token in normalized
        for token in [
            "перенести",
            "перенос",
            "другое время",
            "reschedule",
        ]
    ):
        return "reschedule"
    if any(
        token in normalized
        for token in ["услуги", "что делаете", "services"]
    ):
        return "services"
    if any(
        token in normalized
        for token in ["дорого", "слишком дорого", "expensive"]
    ):
        return "objection_price"
    if any(
        token in normalized
        for token in ["сомневаюсь", "не уверен", "doubt"]
    ):
        return "doubt"
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
        logger.info(
            "choose_reply_template: intent=%s channel=%s key=%s",
            intent,
            channel,
            template.key,
        )
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


def choose_flow_step_template(
    session: Session,
    flow: str,
    step: int,
    channel: str,
) -> Optional[ReplyTemplate]:
    key = _FLOW_STEP_KEY_MAP.get((flow, step))
    if not key:
        return choose_reply_template(session, intent=flow, channel=channel)
    query = select(ReplyTemplate).where(
        and_(
            ReplyTemplate.key == key,
            ReplyTemplate.active.is_(True),
        ),
    )
    channel_filter = or_(
        ReplyTemplate.channel.is_(None),
        ReplyTemplate.channel == channel,
    )
    query = query.where(channel_filter)
    template = session.execute(query).scalars().first()
    if template:
        logger.info(
            "choose_flow_step_template: flow=%s step=%s key=%s",
            flow,
            step,
            template.key,
        )
        return template
    logger.warning(
        "Template for flow=%s step=%s (key=%s) not found; falling back.",
        flow,
        step,
        key,
    )
    return choose_reply_template(session, intent=flow, channel=channel)


def render_template_text(
    template: ReplyTemplate,
    extra: Optional[Mapping[str, str]] = None,
) -> str:
    web_url = settings.web_url
    text = template.text.replace("{web_url}", web_url)
    if extra:
        for key, value in extra.items():
            placeholder = "{" + key + "}"
            text = text.replace(placeholder, value)
    return text


import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

import httpx
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from .config import settings
from .db import session_scope
from .llm import generate_ai_reply
from .models import (
    AvailableSlot,
    Booking,
    Conversation,
    EventLog,
    Lead,
    Message,
    ReminderQueueItem,
)
from .rules_engine import (
    choose_flow_step_template,
    choose_reply_template,
    detect_intent,
    render_template_text,
)
from .compliance import apply_compliance_guard
from .utils.timezone import format_local_datetime, now_utc
logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
_TZ = ZoneInfo(settings.tz)


def _format_dt_local(value: Optional[datetime]) -> str:
    return format_local_datetime(value)


class TelegramClient:
    def __init__(self, token: str) -> None:
        self._token = token
        self._base_url = f"{TELEGRAM_API_BASE}/bot{token}"

    async def _post(
        self,
        method: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self._base_url}/{method}", json=payload)
            response.raise_for_status()
            return response.json()

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return await self._post("sendMessage", payload)

    async def answer_callback_query(self, callback_query_id: str) -> Dict[str, Any]:
        payload = {"callback_query_id": callback_query_id}
        return await self._post("answerCallbackQuery", payload)

    async def set_webhook(self, url: str, secret_token: str) -> Dict[str, Any]:
        payload = {
            "url": url,
            "secret_token": secret_token,
            "allowed_updates": ["message", "callback_query"],
        }
        return await self._post("setWebhook", payload)

    async def delete_webhook(self) -> Dict[str, Any]:
        return await self._post("deleteWebhook", {})

    async def get_updates(
        self,
        offset: Optional[int],
        timeout: int = 20,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"],
        }
        if offset is not None:
            payload["offset"] = offset
        return await self._post("getUpdates", payload)


def _get_or_create_lead_and_conversation(
    session: Session,
    from_user: Dict[str, Any],
    chat_id: int,
) -> Conversation:
    display_name = (
        from_user.get("first_name")
        or from_user.get("username")
        or f"TG_{from_user.get('id')}"
    )
    external_user_id = str(from_user.get("id"))
    external_chat_id = str(chat_id)
    lead = (
        session.query(Lead)
        .filter(Lead.conversations.any(Conversation.external_user_id == external_user_id))
        .first()
    )
    if lead is None:
        lead = Lead(display_name=display_name, status="new")
        session.add(lead)
        session.flush()
    conversation = (
        session.query(Conversation)
        .filter(
            Conversation.lead_id == lead.id,
            Conversation.channel == "telegram",
        )
        .first()
    )
    if conversation is None:
        conversation = Conversation(
            lead_id=lead.id,
            channel="telegram",
            external_user_id=external_user_id,
            external_chat_id=external_chat_id,
        )
        session.add(conversation)
        session.flush()
    return conversation


def _get_state(conversation: Conversation) -> Dict[str, Any]:
    raw = conversation.state or {}
    if not isinstance(raw, dict):
        raw = {}
    state: Dict[str, Any] = {
        "flow": raw.get("flow") or "other",
        "step": int(raw.get("step") or 0),
        "goal": raw.get("goal"),
        "format": raw.get("format"),
        "time_pref": raw.get("time_pref"),
        "slot_id": raw.get("slot_id"),
    }
    conversation.state = state
    return state


def _has_active_booking_flow(state: Dict[str, Any]) -> bool:
    if state.get("flow") != "booking":
        return False
    step = int(state.get("step") or 0)
    return step in (1, 2, 3, 4)


def _reset_conversation_state(conversation: Conversation, reason: str) -> None:
    raw = conversation.state
    if isinstance(raw, dict):
        before = dict(raw)
        raw.clear()
        conversation.state = raw
    else:
        before = raw
        conversation.state = {}
    logger.info(
        "Conversation %s state reset (%s). before=%s after=%s",
        conversation.id,
        reason,
        before,
        conversation.state,
    )


def _build_goal_keyboard() -> Dict[str, Any]:
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Сон и восстановление",
                    "callback_data": "goal:sleep",
                },
                {
                    "text": "Боль / напряжение",
                    "callback_data": "goal:pain",
                },
            ],
            [
                {
                    "text": "Пищеварение",
                    "callback_data": "goal:digestion",
                },
                {
                    "text": "Другое",
                    "callback_data": "goal:other",
                },
            ],
        ],
    }
    return keyboard


def _build_format_keyboard(options: Optional[list[str]] = None) -> Dict[str, Any]:
    values = options or settings.allowed_formats_list
    valid = [value for value in values if value in {"online", "offline"}]
    if not valid:
        valid = ["offline", "online"]
    buttons = []
    for value in valid:
        if value == "offline":
            text = "Очный формат (офлайн)"
        else:
            text = "Онлайн"
        buttons.append(
            {
                "text": text,
                "callback_data": f"format:{value}",
            },
        )
    keyboard = {"inline_keyboard": [[button] for button in buttons]}
    return keyboard


def _build_time_keyboard(options: Optional[list[str]] = None) -> Dict[str, Any]:
    values = options or settings.allowed_time_prefs_list
    valid = [value for value in values if value in {"day", "evening"}]
    if not valid:
        valid = ["day", "evening"]
    buttons = []
    for value in valid:
        if value == "day":
            text = "Днём"
        else:
            text = "Вечером"
        buttons.append(
            {
                "text": text,
                "callback_data": f"time:{value}",
            },
        )
    keyboard = {"inline_keyboard": [[button] for button in buttons]}
    return keyboard


def _slot_local_hour(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    local = value.astimezone(_TZ)
    return local.hour


def _is_global_intent(normalized_text: str, intent: str) -> bool:
    if not normalized_text:
        return False
    if normalized_text.startswith("/start") or normalized_text.startswith("/reset"):
        return True
    if intent in {"price", "booking", "reschedule"}:
        return True
    return False


def _select_top_slots(
    session: Session,
    time_pref: Optional[str],
) -> list[AvailableSlot]:
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
    result: list[AvailableSlot] = []
    for slot in candidates:
        hour = _slot_local_hour(slot.starts_at)
        if time_pref == "day":
            if (
                hour >= settings.day_start_hour
                and hour < settings.day_end_hour
            ):
                result.append(slot)
        elif time_pref == "evening":
            if hour >= settings.day_end_hour:
                result.append(slot)
        else:
            result.append(slot)
        if len(result) >= 3:
            break
    return result


def _select_reschedule_slots(
    session: Session,
    current_slot: AvailableSlot,
    limit: int = 3,
) -> list[AvailableSlot]:
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
    slots = query.limit(limit).all()
    return slots


def _build_slots_keyboard(slots: list[AvailableSlot]) -> Dict[str, Any]:
    rows = []
    for slot in slots:
        label = _format_dt_local(slot.starts_at)
        rows.append(
            [
                {
                    "text": label,
                    "callback_data": f"slot:{slot.id}",
                },
            ],
        )
    return {"inline_keyboard": rows}


def _build_reschedule_slots_keyboard(
    slots: list[AvailableSlot],
) -> Dict[str, Any]:
    rows = []
    for slot in slots:
        label = _format_dt_local(slot.starts_at)
        rows.append(
            [
                {
                    "text": label,
                    "callback_data": f"reslot:{slot.id}",
                },
            ],
        )
    return {"inline_keyboard": rows}


def _build_ping_keyboard() -> Dict[str, Any]:
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Ping",
                    "callback_data": "ping",
                },
            ],
        ],
    }
    return keyboard


def _build_main_menu_keyboard() -> Dict[str, Any]:
    web_url = settings.web_url
    web_button: Dict[str, Any] = {
        "text": "Оставить заявку на сайте",
        "url": web_url,
    } if web_url else {}

    rows: list[list[Dict[str, Any]]] = [
        [
            {
                "text": "Записаться",
                "callback_data": "main:booking",
            },
            {
                "text": "Цена",
                "callback_data": "main:price",
            },
        ],
        [
            {
                "text": "Как проходит приём",
                "callback_data": "main:how",
            },
            {
                "text": "Где принимаете",
                "callback_data": "main:where",
            },
        ],
    ]

    if web_button:
        rows.append([web_button])

    keyboard = {"inline_keyboard": rows}
    return keyboard


def _build_prefill_url(
    goal: Optional[str],
    fmt: Optional[str],
    time_pref: Optional[str],
) -> Optional[str]:
    from urllib.parse import urlencode

    params: Dict[str, str] = {}
    if goal:
        params["goal"] = goal
    if fmt:
        params["format"] = fmt
    if time_pref:
        params["time"] = time_pref
    if not params:
        return None
    base = settings.web_url
    return f"{base}?{urlencode(params)}"


def _start_booking_flow(
    session: Session,
    conversation: Conversation,
    state: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    state.clear()
    state.update(
        {
            "flow": "booking",
            "step": 1,
            "goal": None,
            "format": None,
            "time_pref": None,
            "slot_id": None,
        },
    )
    template = choose_flow_step_template(
        session,
        flow="booking",
        step=1,
        channel="telegram",
    )
    if template is None:
        text = (
            "Давайте подберём запись. "
            "Выберите, пожалуйста, основной запрос с помощью кнопок."
        )
    else:
        text = render_template_text(template)
    keyboard = _build_goal_keyboard()
    return text, keyboard


def _start_price_flow(
    session: Session,
    conversation: Conversation,
    state: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    state.clear()
    state.update(
        {
            "flow": "price",
            "step": 1,
            "goal": None,
            "format": None,
            "time_pref": None,
            "slot_id": None,
        },
    )
    template = choose_flow_step_template(
        session,
        flow="price",
        step=1,
        channel="telegram",
    )
    if template is None:
        text = (
            "Чтобы подсказать по форматам и ориентировочной стоимости, "
            "выберите, пожалуйста, что сейчас важнее всего."
        )
    else:
        text = render_template_text(template)
    keyboard = _build_goal_keyboard()
    return text, keyboard


def _continue_booking_after_goal(
    session: Session,
    conversation: Conversation,
    state: Dict[str, Any],
) -> Tuple[str, Optional[Dict[str, Any]]]:
    formats = settings.allowed_formats_list
    valid = [value for value in formats if value in {"online", "offline"}]
    if not valid:
        valid = ["offline", "online"]
    if len(valid) == 1:
        state["format"] = valid[0]
        return _continue_booking_after_format(session, conversation, state)
    state["step"] = 2
    template = choose_flow_step_template(
        session,
        flow="booking",
        step=2,
        channel="telegram",
    )
    if template is None:
        text = (
            "Выберите, пожалуйста, формат встречи: "
            "онлайн или очный (офлайн)."
        )
    else:
        text = render_template_text(template)
    keyboard = _build_format_keyboard(valid)
    return text, keyboard


def _continue_booking_after_format(
    session: Session,
    conversation: Conversation,
    state: Dict[str, Any],
) -> Tuple[str, Optional[Dict[str, Any]]]:
    prefs = settings.allowed_time_prefs_list
    valid = [value for value in prefs if value in {"day", "evening"}]
    if not valid:
        valid = ["day", "evening"]
    if len(valid) == 1:
        state["time_pref"] = valid[0]
        return _continue_booking_after_time(session, conversation, state)
    state["step"] = 3
    template = choose_flow_step_template(
        session,
        flow="booking",
        step=3,
        channel="telegram",
    )
    if template is None:
        text = (
            "Когда вам удобнее? Выберите, пожалуйста, "
            "днём или ближе к вечеру."
        )
    else:
        text = render_template_text(template)
    keyboard = _build_time_keyboard(valid)
    return text, keyboard


def _continue_booking_after_time(
    session: Session,
    conversation: Conversation,
    state: Dict[str, Any],
) -> Tuple[str, Optional[Dict[str, Any]]]:
    time_pref = state.get("time_pref") or "day"
    slots = _select_top_slots(session, time_pref=time_pref)
    template = choose_flow_step_template(
        session,
        flow="booking",
        step=4,
        channel="telegram",
    )
    if template is None:
        text = "Предлагаю ближайшие варианты времени. Выберите слот кнопкой."
    else:
        text = render_template_text(template)
    prefill_url = _build_prefill_url(
        goal=state.get("goal"),
        fmt=state.get("format"),
        time_pref=time_pref,
    )
    if prefill_url:
        text = (
            f"{text}\n\nЕсли удобнее через веб-форму, "
            f"можно оставить заявку здесь: {prefill_url}"
        )
    state["step"] = 4
    if not slots:
        return (
            f"{text}\n\nСейчас нет свободных слотов по выбранным фильтрам.",
            None,
        )
    keyboard = _build_slots_keyboard(slots)
    return text, keyboard


def _continue_price_after_goal(
    session: Session,
    conversation: Conversation,
    state: Dict[str, Any],
) -> Tuple[str, Optional[Dict[str, Any]]]:
    template = choose_flow_step_template(
        session,
        flow="price",
        step=1,
        channel="telegram",
    )
    if template is None:
        template = choose_reply_template(
            session,
            intent="price",
            channel="telegram",
        )
    if template is None:
        logger.warning("No template for price flow; skipping auto-reply.")
        return "", None
    text = render_template_text(template)
    prefill_url = _build_prefill_url(
        goal=state.get("goal"),
        fmt=None,
        time_pref=None,
    )
    if prefill_url:
        text = (
            f"{text}\n\nЕсли захотите оставить заявку, "
            f"можно сделать это через веб-форму: {prefill_url}"
        )
    state["step"] = 0
    state["flow"] = "other"
    return text, None


def _create_booking_for_slot(
    session: Session,
    conversation: Conversation,
    state: Dict[str, Any],
    slot_id: str,
) -> str:
    logger.info("Slot selection received: raw_slot_id=%s", slot_id)
    try:
        slot_uuid = UUID(slot_id)
    except ValueError:
        logger.warning("Invalid slot UUID: %s", slot_id)
        return (
            "Не получилось распознать выбранный слот. "
            "Попробуйте выбрать время ещё раз или начните заново командой /start."
        )

    try:
        slot = (
            session.query(AvailableSlot)
            .with_for_update()
            .filter(
                AvailableSlot.id == slot_uuid,
                AvailableSlot.is_active.is_(True),
            )
            .first()
        )
        if slot is None:
            logger.info("Slot %s not found or inactive.", slot_uuid)
            return (
                "Этот слот уже недоступен. "
                "Пожалуйста, выберите другое время."
            )
        if slot.reserved_count >= slot.capacity:
            logger.info(
                "Slot %s is full: reserved_count=%s capacity=%s",
                slot.id,
                slot.reserved_count,
                slot.capacity,
            )
            return (
                "Этот слот уже занят. "
                "Пожалуйста, выберите другое время из доступных вариантов."
            )

        slot.reserved_count += 1

        lead = conversation.lead
        scheduled_at = slot.starts_at
        booking = Booking(
            lead_id=lead.id,
            offer_id=None,
            slot_id=slot.id,
            status="requested",
            scheduled_at=scheduled_at,
            contact_name=lead.display_name,
            contact_phone=lead.phone or "",
            contact_message=None,
            source="telegram",
        )
        session.add(booking)
        session.flush()

        logger.info(
            "Created booking id=%s for lead_id=%s slot_id=%s",
            booking.id,
            lead.id,
            slot.id,
        )

        event = EventLog(
            event_type="booking_created",
            payload={
                "booking_id": str(booking.id),
                "lead_id": str(lead.id),
                "slot_id": str(slot.id),
                "source": "telegram",
            },
        )
        session.add(event)

        if (
            settings.reminder_enabled
            and scheduled_at is not None
            and booking
            and booking.id
        ):
            for hours_before in (
                settings.reminder_1_hours_before,
                settings.reminder_2_hours_before,
            ):
                if hours_before <= 0:
                    continue
                remind_at = scheduled_at - timedelta(hours=hours_before)
                if remind_at <= now_utc():
                    continue
                logger.info(
                    "Creating reminder for booking_id=%s at %s "
                    "(hours_before=%s)",
                    booking.id,
                    remind_at,
                    hours_before,
                )
                reminder = ReminderQueueItem(
                    booking_id=booking.id,
                    remind_at=remind_at,
                )
                session.add(reminder)
        elif settings.reminder_enabled:
            logger.warning(
                "Skipping reminder creation: booking or booking.id is missing "
                "(booking=%s, id=%s)",
                booking,
                getattr(booking, "id", None),
            )

        state.clear()
        state.update(
            {
                "flow": "other",
                "step": 0,
                "goal": None,
                "format": None,
                "time_pref": None,
                "slot_id": str(slot.id),
            },
        )
        _reset_conversation_state(conversation, "booking_completed")

        date_time = _format_dt_local(scheduled_at)
        text = (
            "Заявка на запись принята на {date_time}. "
            "Подтвержу в ближайшее время."
        ).format(date_time=date_time)
        logger.info(
            "Booking flow completed successfully for conversation_id=%s",
            conversation.id,
        )
        return text
    except Exception as exc:
        logger.error(
            "Failed to create booking or reminder for slot %s: %s",
            slot_id,
            exc,
            exc_info=True,
        )
        session.rollback()
        state["flow"] = "booking_error"
        state["step"] = 0
        state["slot_id"] = None
        return (
            "Не получилось завершить запись. "
            "Попробуйте ещё раз или начните заново командой /start."
        )


async def handle_telegram_update(update: Dict[str, Any], client: TelegramClient) -> None:
    update_id = update.get("update_id")
    callback = update.get("callback_query")
    message = update.get("message")
    update_type = "callback_query" if callback else "message" if message else "other"
    logger.info("Received update %s of type %s", update_id, update_type)

    if callback:
        await _handle_callback_query(callback, client)
        return

    if not message:
        return
    raw_text = message.get("text") or ""
    chat = message.get("chat") or {}
    from_user = message.get("from") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    normalized_text = raw_text.strip().casefold()
    logger.info(
        "Received message from chat_id=%s raw=%r normalized=%r",
        chat_id,
        raw_text,
        normalized_text,
    )

    safe_text: Optional[str] = None
    reply_markup: Optional[Dict[str, Any]] = None
    outbound_id: Optional[UUID] = None

    with session_scope() as session:
        conversation = _get_or_create_lead_and_conversation(
            session,
            from_user,
            chat_id,
        )
        lead = conversation.lead
        inbound = Message(
            conversation_id=conversation.id,
            lead_id=lead.id,
            channel="telegram",
            direction="inbound",
            text=raw_text,
            delivery_status="sent",
        )
        session.add(inbound)
        lead.last_message_at = inbound.created_at
        conversation.last_inbound_at = inbound.created_at

        state = _get_state(conversation)
        intent = detect_intent(raw_text)
        logger.info("faq intent selected: %s", intent)

        logger.info(
            "Message routing: flow=%s step=%s intent=%s",
            state.get("flow"),
            state.get("step"),
            intent,
        )

        global_override = _is_global_intent(normalized_text, intent)
        logger.info(
            "Global intent check: override=%s for intent=%s normalized=%r",
            global_override,
            intent,
            normalized_text,
        )

        reply_text: str = ""

        if normalized_text == "ping":
            reply_text = "Нажмите кнопку Ping"
            reply_markup = _build_ping_keyboard()
        elif normalized_text.startswith("/reset"):
            _reset_conversation_state(conversation, "manual_reset")
            reply_text = (
                "Сценарий сброшен. "
                "Можно начать заново — напишите «записаться» или используйте /start."
            )
        elif normalized_text.startswith("/start"):
            _reset_conversation_state(conversation, "start_command")
            greeting = (
                "Привет! Я помогу записаться на приём и ответить "
                "на частые вопросы.\n\n"
            )
            step_text, reply_markup = _start_booking_flow(
                session,
                conversation,
                state,
            )
            reply_text = f"{greeting}{step_text}"
        elif _has_active_booking_flow(state) and not global_override:
            if (
                state.get("flow") == "booking"
                and int(state.get("step") or 0) == 1
                and not state.get("goal")
            ):
                logger.info(
                    "Booking flow step=1 without goal for conversation %s; "
                    "re-sending goal keyboard.",
                    conversation.id,
                )
                reply_text, reply_markup = _start_booking_flow(
                    session,
                    conversation,
                    state,
                )
            else:
                logger.info(
                    "Booking flow already active for conversation %s; "
                    "waiting for button actions.",
                    conversation.id,
                )
        elif intent == "booking":
            reply_text, reply_markup = _start_booking_flow(
                session,
                conversation,
                state,
            )
        elif intent == "price":
            reply_text, reply_markup = _start_price_flow(
                session,
                conversation,
                state,
            )
        elif intent == "reschedule":
            logger.info(
                "reschedule flow started for conversation_id=%s lead_id=%s",
                conversation.id,
                lead.id,
            )
            from .models import Booking  # local import to avoid circular at top level

            now = now_utc()
            booking = (
                session.query(Booking)
                .filter(
                    Booking.lead_id == lead.id,
                    Booking.status.in_(("requested", "confirmed")),
                    Booking.scheduled_at.is_not(None),
                    Booking.scheduled_at >= now,
                )
                .order_by(Booking.scheduled_at.asc())
                .first()
            )
            if booking is None or booking.slot_id is None:
                logger.info(
                    "No active booking found for reschedule (lead_id=%s).",
                    lead.id,
                )
                reply_text = (
                    "У вас сейчас нет активной записи. "
                    "Могу помочь записаться заново."
                )
            else:
                logger.info(
                    "Active booking found for reschedule: booking_id=%s "
                    "lead_id=%s scheduled_at=%s",
                    booking.id,
                    lead.id,
                    booking.scheduled_at,
                )
                current_slot = (
                    session.query(AvailableSlot)
                    .filter(AvailableSlot.id == booking.slot_id)
                    .first()
                )
                slots: list[AvailableSlot] = []
                if current_slot is not None:
                    slots = _select_reschedule_slots(session, current_slot)
                date_time = _format_dt_local(booking.scheduled_at)
                template = choose_flow_step_template(
                    session,
                    flow="reschedule",
                    step=1,
                    channel="telegram",
                )
                if template is None:
                    reply_text = (
                        "Сейчас у вас есть активная запись на {date_time}. "
                        "Я могу предложить несколько ближайших свободных "
                        "слотов для переноса."
                    ).format(date_time=date_time)
                else:
                    reply_text = render_template_text(
                        template,
                        extra={"date_time": date_time},
                    )
                if slots:
                    reply_markup = _build_reschedule_slots_keyboard(
                        slots=slots,
                    )
                    logger.info(
                        "Prepared %s reschedule slots for booking_id=%s.",
                        len(slots),
                        booking.id,
                    )
                else:
                    logger.info(
                        "No alternative slots available for reschedule "
                        "(booking_id=%s).",
                        booking.id,
                    )
        else:
            template = choose_reply_template(
                session,
                intent=intent,
                channel="telegram",
            )
            if template is None:
                logger.warning(
                    "No template found for intent=%s; trying LLM fallback.",
                    intent,
                )
                llm_context: dict[str, object] = {
                    "intent": intent,
                    "channel": "telegram",
                }
                llm_reply = generate_ai_reply(llm_context, raw_text)
                if llm_reply:
                    reply_text = llm_reply
                else:
                    logger.info(
                        "LLM fallback did not produce reply; "
                        "sending generic help.",
                    )
                    reply_text = (
                        "Я могу помочь с записью и вопросами "
                        "о форматах.\n\n"
                        "Напишите «записаться» или «цена», "
                        "или оставьте заявку через веб-форму: "
                        f"{settings.web_url}"
                    )
            else:
                reply_text = render_template_text(template)

        if reply_text:
            safe_text = apply_compliance_guard(reply_text)
            outbound = Message(
                conversation_id=conversation.id,
                lead_id=lead.id,
                channel="telegram",
                direction="outbound",
                text=safe_text,
                delivery_status="unknown",
            )
            session.add(outbound)
            session.flush()
            outbound_id = outbound.id
            logger.info(
                "Prepared outbound message id=%s for chat_id=%s",
                outbound_id,
                chat_id,
            )

    if not safe_text or outbound_id is None:
        return

    delivery_status = "failed"
    delivery_error = None
    try:
        response = await client.send_message(
            chat_id=str(chat_id),
            text=safe_text,
            reply_markup=reply_markup,
        )
        if response.get("ok"):
            delivery_status = "sent"
        else:
            delivery_error = str(response)
    except Exception as exc:
        delivery_error = str(exc)
        logger.error("Failed to send Telegram message: %s", exc)

    with session_scope() as session:
        msg = session.get(Message, outbound_id)
        if msg is not None:
            msg.delivery_status = delivery_status
            msg.delivery_error = delivery_error


async def _handle_callback_query(
    callback: Dict[str, Any],
    client: TelegramClient,
) -> None:
    data = callback.get("data") or ""
    message = callback.get("message") or {}
    chat = message.get("chat") or {}
    from_user = callback.get("from") or {}
    chat_id = chat.get("id")
    callback_id = callback.get("id")
    if chat_id is None:
        return

    logger.info("Handling callback_query with data=%s", data)

    safe_text: Optional[str] = None
    reply_markup: Optional[Dict[str, Any]] = None
    outbound_id: Optional[UUID] = None

    with session_scope() as session:
        conversation = _get_or_create_lead_and_conversation(
            session,
            from_user,
            chat_id,
        )
        lead = conversation.lead
        inbound = Message(
            conversation_id=conversation.id,
            lead_id=lead.id,
            channel="telegram",
            direction="inbound",
            text=data,
            delivery_status="sent",
        )
        session.add(inbound)
        lead.last_message_at = inbound.created_at
        conversation.last_inbound_at = inbound.created_at

        state = _get_state(conversation)
        flow = state.get("flow") or "other"

        logger.info(
            "Callback routing: flow=%s step=%s data=%s state_before=%s",
            flow,
            state.get("step"),
            data,
            state,
        )

        reply_text: str = ""

        if data == "ping":
            reply_text = "OK"
        elif data == "main:booking":
            reply_text, reply_markup = _start_booking_flow(
                session,
                conversation,
                state,
            )
            logger.info(
                "Main menu: booking selected for conversation_id=%s",
                conversation.id,
            )
        elif data == "main:price":
            reply_text, reply_markup = _start_price_flow(
                session,
                conversation,
                state,
            )
            logger.info(
                "Main menu: price selected for conversation_id=%s",
                conversation.id,
            )
        elif data == "main:how":
            template = choose_reply_template(
                session,
                intent="how_it_works",
                channel="telegram",
            )
            if template is None:
                logger.info(
                    "No template for how_it_works; falling back to generic text.",
                )
                reply_text = (
                    "На приёме мы спокойно разбираем ваш запрос, "
                    "собираем важную информацию и подбираем формат "
                    "работы под вашу ситуацию.\n\n"
                    "Если хотите, могу сразу помочь с записью — "
                    "нажмите «Записаться» или воспользуйтесь веб-формой: "
                    f"{settings.web_url}"
                )
            else:
                reply_text = render_template_text(template)
            logger.info(
                "Main menu: how_it_works selected for conversation_id=%s",
                conversation.id,
            )
        elif data == "main:where":
            template = choose_reply_template(
                session,
                intent="location",
                channel="telegram",
            )
            if template is None:
                logger.info(
                    "No template for location; falling back to generic text.",
                )
                base = (
                    "Приём проходит в офлайн-кабинете или онлайн — "
                    "в зависимости от выбранного формата."
                )
                if settings.web_url:
                    reply_text = (
                        f"{base}\n\nТочный адрес и варианты записи можно "
                        f"уточнить через веб-форму: {settings.web_url}"
                    )
                else:
                    reply_text = base
            else:
                reply_text = render_template_text(template)
            logger.info(
                "Main menu: location selected for conversation_id=%s",
                conversation.id,
            )
        elif data.startswith("goal:"):
            goal = data.split(":", 1)[1]
            state["goal"] = goal

            auto_format = False
            auto_time = False

            if flow not in {"booking", "price"}:
                # если по какой-то причине flow потерялся – считаем, что это booking
                flow = "booking"
                state["flow"] = "booking"
                state["step"] = state.get("step") or 1

            if flow == "booking":
                # до вызова шага запомним формат/время
                before_format = state.get("format")
                before_time = state.get("time_pref")

                reply_text, reply_markup = _continue_booking_after_goal(
                    session,
                    conversation,
                    state,
                )

                after_format = state.get("format")
                after_time = state.get("time_pref")
                auto_format = bool(after_format and after_format != before_format)
                auto_time = bool(after_time and after_time != before_time)

                logger.info(
                    "Booking goal callback: goal=%s auto_format=%s auto_time=%s "
                    "state_after=%s",
                    goal,
                    auto_format,
                    auto_time,
                    state,
                )
            elif flow == "price":
                reply_text, reply_markup = _continue_price_after_goal(
                    session,
                    conversation,
                    state,
                )
                logger.info(
                    "Price goal callback: goal=%s state_after=%s",
                    goal,
                    state,
                )
        elif data.startswith("format:") and flow == "booking":
            fmt = data.split(":", 1)[1]
            state["format"] = fmt
            reply_text, reply_markup = _continue_booking_after_format(
                session,
                conversation,
                state,
            )
            logger.info(
                "Format callback: format=%s state_after=%s",
                fmt,
                state,
            )
        elif data.startswith("time:") and flow == "booking":
            time_pref = data.split(":", 1)[1]
            state["time_pref"] = time_pref
            reply_text, reply_markup = _continue_booking_after_time(
                session,
                conversation,
                state,
            )
            logger.info(
                "Time callback: time_pref=%s state_after=%s",
                time_pref,
                state,
            )
        elif data.startswith("slot:") and flow == "booking":
            slot_raw = data.split(":", 1)[1]
            reply_text = _create_booking_for_slot(
                session,
                conversation,
                state,
                slot_raw,
            )
            logger.info(
                "Slot callback: slot_id=%s state_after=%s",
                slot_raw,
                state,
            )
        elif data.startswith("reslot:"):
            parts = data.split(":", 1)
            if len(parts) != 2:
                logger.warning("Invalid reslot callback format: %s", data)
            else:
                _, slot_raw = parts
                from .models import Booking  # local import to avoid circular

                logger.info(
                    "Reschedule callback received for conversation_id=%s "
                    "new_slot_id=%s",
                    conversation.id,
                    slot_raw,
                )
                try:
                    new_slot_id = UUID(slot_raw)
                except ValueError:
                    logger.warning(
                        "Invalid slot UUID in reslot callback: slot_id=%s",
                        slot_raw,
                    )
                    reply_text = (
                        "Не получилось обработать выбор нового времени. "
                        "Попробуйте ещё раз написать «перенести»."
                    )
                else:
                    now = now_utc()
                    booking = (
                        session.query(Booking)
                        .with_for_update()
                        .filter(
                            Booking.lead_id == lead.id,
                            Booking.status.in_(("requested", "confirmed")),
                            Booking.scheduled_at.is_not(None),
                            Booking.scheduled_at >= now,
                        )
                        .order_by(Booking.scheduled_at.asc())
                        .first()
                    )
                    if booking is None:
                        logger.info(
                            "No active booking found for reschedule callback "
                            "(lead_id=%s).",
                            lead.id,
                        )
                        reply_text = (
                            "Сейчас нет активной записи, которую можно "
                            "перенести. Если актуально, можно создать новую "
                            "запись."
                        )
                    elif booking.slot_id is None:
                        logger.info(
                            "Booking %s has no slot_id; cannot reschedule.",
                            booking.id,
                        )
                        reply_text = (
                            "Эту запись нельзя перенести автоматически. "
                            "Пожалуйста, свяжитесь с администратором."
                        )
                    else:
                        current_slot = (
                            session.query(AvailableSlot)
                            .with_for_update()
                            .filter(AvailableSlot.id == booking.slot_id)
                            .first()
                        )
                        new_slot = (
                            session.query(AvailableSlot)
                            .with_for_update()
                            .filter(
                                AvailableSlot.id == new_slot_id,
                                AvailableSlot.is_active.is_(True),
                                AvailableSlot.reserved_count
                                < AvailableSlot.capacity,
                                AvailableSlot.starts_at > now,
                            )
                            .first()
                        )
                        if new_slot is None:
                            logger.info(
                                "New slot for reschedule is not available: %s",
                                new_slot_id,
                            )
                            reply_text = (
                                "Этот слот уже недоступен. "
                                "Попробуйте ещё раз написать «перенести» — "
                                "я подберу другие варианты."
                            )
                        else:
                            if (
                                current_slot is not None
                                and current_slot.reserved_count > 0
                            ):
                                current_slot.reserved_count -= 1
                                logger.info(
                                    "Old slot released for booking_id=%s "
                                    "slot_id=%s reserved_count=%s",
                                    booking.id,
                                    current_slot.id,
                                    current_slot.reserved_count,
                                )
                            new_slot.reserved_count += 1
                            logger.info(
                                "New slot reserved for booking_id=%s "
                                "slot_id=%s reserved_count=%s",
                                booking.id,
                                new_slot.id,
                                new_slot.reserved_count,
                            )

                            booking.slot_id = new_slot.id
                            booking.scheduled_at = new_slot.starts_at

                            cancelled = (
                                session.query(ReminderQueueItem)
                                .with_for_update()
                                .filter(
                                    ReminderQueueItem.booking_id == booking.id,
                                    ReminderQueueItem.status == "pending",
                                )
                                .all()
                            )
                            for item in cancelled:
                                item.status = "cancelled"
                                item.last_error = "rescheduled"
                            logger.info(
                                "Cancelled %s pending reminders for "
                                "booking_id=%s due to reschedule.",
                                len(cancelled),
                                booking.id,
                            )

                            if (
                                settings.reminder_enabled
                                and booking.scheduled_at is not None
                            ):
                                created = 0
                                for hours_before in (
                                    settings.reminder_1_hours_before,
                                    settings.reminder_2_hours_before,
                                ):
                                    if hours_before <= 0:
                                        continue
                                    remind_at = booking.scheduled_at - timedelta(
                                        hours=hours_before,
                                    )
                                    if remind_at <= now_utc():
                                        continue
                                    reminder = ReminderQueueItem(
                                        booking_id=booking.id,
                                        remind_at=remind_at,
                                    )
                                    session.add(reminder)
                                    created += 1
                                logger.info(
                                    "Reminders recreated for booking_id=%s "
                                    "count=%s",
                                    booking.id,
                                    created,
                                )

                            date_time = _format_dt_local(booking.scheduled_at)
                            template = choose_flow_step_template(
                                session,
                                flow="reschedule",
                                step=3,
                                channel="telegram",
                            )
                            if template is None:
                                reply_text = (
                                    "Запись перенесена на {date_time}."
                                ).format(date_time=date_time)
                            else:
                                reply_text = render_template_text(
                                    template,
                                    extra={"date_time": date_time},
                                )
        else:
            logger.info("Unknown callback data received: %s", data)

        if reply_text:
            safe_text = apply_compliance_guard(reply_text)
            outbound = Message(
                conversation_id=conversation.id,
                lead_id=lead.id,
                channel="telegram",
                direction="outbound",
                text=safe_text,
                delivery_status="unknown",
            )
            session.add(outbound)
            session.flush()
            outbound_id = outbound.id
            logger.info(
                "Prepared outbound callback message id=%s for chat_id=%s",
                outbound_id,
                chat_id,
            )

    if callback_id:
        try:
            await client.answer_callback_query(str(callback_id))
        except Exception as exc:
            logger.warning("Failed to answer callback query: %s", exc)

    if not safe_text or outbound_id is None:
        return

    delivery_status = "failed"
    delivery_error = None
    try:
        logger.info(
            "Sending callback response message to chat_id=%s text=%r",
            chat_id,
            safe_text,
        )
        response = await client.send_message(
            chat_id=str(chat_id),
            text=safe_text,
            reply_markup=reply_markup,
        )
        if response.get("ok"):
            delivery_status = "sent"
        else:
            delivery_error = str(response)
    except Exception as exc:
        delivery_error = str(exc)
        logger.error("Failed to send Telegram message: %s", exc)

    with session_scope() as session:
        msg = session.get(Message, outbound_id)
        if msg is not None:
            msg.delivery_status = delivery_status
            msg.delivery_error = delivery_error


async def polling_loop() -> None:
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not set; polling disabled.")
        return
    client = TelegramClient(settings.telegram_bot_token)
    offset: Optional[int] = None
    logger.info("Starting Telegram polling loop.")
    while True:
        try:
            data = await client.get_updates(offset=offset)
            if not data.get("ok"):
                await asyncio.sleep(5)
                continue
            updates = data.get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                await handle_telegram_update(update, client)
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 409:
                logger.warning(
                    "Telegram polling received 409 Conflict (webhook is likely set); "
                    "polling loop will sleep for 60 seconds.",
                )
                await asyncio.sleep(60)
                continue
            logger.error("Error in Telegram polling loop (HTTP %s): %s", status_code, exc)
            await asyncio.sleep(5)
        except Exception as exc:
            logger.error("Error in Telegram polling loop: %s", exc)
            await asyncio.sleep(5)


async def ensure_webhook() -> None:
    if not settings.telegram_bot_token or not settings.telegram_webhook_url:
        return
    client = TelegramClient(settings.telegram_bot_token)
    try:
        result = await client.set_webhook(
            url=settings.telegram_webhook_url,
            secret_token=settings.telegram_webhook_secret,
        )
        logger.info("Telegram setWebhook result: %s", result)
    except Exception as exc:
        logger.error("Failed to set Telegram webhook: %s", exc)



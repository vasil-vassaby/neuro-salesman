import asyncio
import logging
from typing import Optional

from .config import settings
from .db import session_scope
from .models import Booking, Conversation, EventLog, Message, ReminderQueueItem
from .telegram_bot import TelegramClient
from .time_utils import format_local_time
from .utils.timezone import format_local_datetime, now_utc


logger = logging.getLogger(__name__)


CONFIRM_TEXT_TEMPLATE = (
    "Запись подтверждена: {date_time}. "
    "Если нужно перенести — ответьте на это сообщение."
)

REMINDER_24H_TEXT_TEMPLATE = (
    "Напоминание: завтра у вас запись {date_time}."
)

REMINDER_2H_TEXT_TEMPLATE = (
    "Напоминаю: запись сегодня в {time}."
)


def _format_dt(value) -> str:
    return format_local_datetime(value)


def _format_time(value) -> str:
    return format_local_time(value)


async def _send_telegram_message(chat_id: str, text: str) -> tuple[str, Optional[str]]:
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not set; skipping send.")
        return "failed", "Telegram bot not configured"
    client = TelegramClient(settings.telegram_bot_token)
    try:
        response = await client.send_message(chat_id=chat_id, text=text)
        if response.get("ok"):
            return "sent", None
        return "failed", str(response)
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Failed to send Telegram message: %s", exc)
        return "failed", str(exc)


async def reminders_loop() -> None:
    if not settings.reminder_enabled:
        logger.info("Reminders are disabled; loop will not start.")
        return
    logger.info("Starting reminders loop...")
    while True:
        now = now_utc()
        try:
            with session_scope() as session:
                items = (
                    session.query(ReminderQueueItem)
                    .filter(
                        ReminderQueueItem.status == "pending",
                        ReminderQueueItem.remind_at <= now,
                    )
                    .all()
                )
                for item in items:
                    booking = session.get(Booking, item.booking_id)
                    if booking is None or booking.scheduled_at is None:
                        item.status = "failed"
                        item.last_error = "Booking missing or has no scheduled_at"
                        continue

                    if booking.status != "confirmed":
                        item.status = "failed"
                        item.last_error = "Booking is not confirmed"
                        continue

                    delta = booking.scheduled_at - item.remind_at
                    hours_before = int(delta.total_seconds() // 3600)
                    if abs(hours_before - settings.reminder_2_hours_before) <= 1:
                        text = REMINDER_2H_TEXT_TEMPLATE.format(
                            time=_format_time(booking.scheduled_at),
                        )
                    else:
                        text = REMINDER_24H_TEXT_TEMPLATE.format(
                            date_time=_format_dt(booking.scheduled_at),
                        )
                    chat_id: Optional[str] = None
                    conversation = (
                        session.query(Conversation)
                        .filter(
                            Conversation.lead_id == booking.lead_id,
                            Conversation.channel == "telegram",
                        )
                        .first()
                    )
                    if conversation is not None:
                        chat_id = conversation.external_chat_id

                    delivery_status = "sent"
                    delivery_error: Optional[str] = None

                    if chat_id and settings.telegram_bot_token:
                        outbound = Message(
                            conversation_id=conversation.id,
                            lead_id=booking.lead_id,
                            channel="telegram",
                            direction="outbound",
                            text=text,
                            delivery_status="unknown",
                        )
                        session.add(outbound)
                        session.flush()

                        delivery_status, delivery_error = await _send_telegram_message(
                            chat_id=str(chat_id),
                            text=text,
                        )
                        stored = session.get(Message, outbound.id)
                        if stored is not None:
                            stored.delivery_status = delivery_status
                            stored.delivery_error = delivery_error
                    else:
                        logger.info(
                            "No Telegram channel for lead %s; "
                            "marking reminder as sent only in logs.",
                            booking.lead_id,
                        )
                        delivery_status = "sent"
                        delivery_error = "No telegram channel; logged only"

                    item.status = "sent" if delivery_status == "sent" else "failed"
                    item.last_error = delivery_error

                    event = EventLog(
                        event_type="reminder_processed",
                        payload={
                            "booking_id": str(booking.id),
                            "reminder_id": str(item.id),
                            "status": item.status,
                            "delivery_status": delivery_status,
                        },
                    )
                    session.add(event)
        except Exception as exc:  # pragma: no cover - safety net
            logger.error("Error in reminders loop: %s", exc)

        await asyncio.sleep(60)


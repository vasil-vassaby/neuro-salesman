import asyncio
import logging
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from .config import settings
from .db import session_scope
from .models import Conversation, Lead, Message
from .rules_engine import choose_reply_template, detect_intent, render_template_text
from .compliance import apply_compliance_guard


logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


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
    ) -> Dict[str, Any]:
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        return await self._post("sendMessage", payload)

    async def set_webhook(self, url: str, secret_token: str) -> Dict[str, Any]:
        payload = {
            "url": url,
            "secret_token": secret_token,
            "allowed_updates": ["message"],
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
            "allowed_updates": ["message"],
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


async def handle_telegram_update(update: Dict[str, Any], client: TelegramClient) -> None:
    message = update.get("message")
    if not message:
        return
    text = message.get("text") or ""
    chat = message.get("chat") or {}
    from_user = message.get("from") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    with session_scope() as session:
        conversation = _get_or_create_lead_and_conversation(session, from_user, chat_id)
        lead = conversation.lead
        inbound = Message(
            conversation_id=conversation.id,
            lead_id=lead.id,
            channel="telegram",
            direction="inbound",
            text=text,
            delivery_status="sent",
        )
        session.add(inbound)
        lead.last_message_at = inbound.created_at
        conversation.last_inbound_at = inbound.created_at

        intent = detect_intent(text)
        template = choose_reply_template(session, intent=intent, channel="telegram")
        if template is None:
            logger.warning("No template found; skipping auto-reply.")
            return
        reply_text = render_template_text(template)
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

    delivery_status = "failed"
    delivery_error = None
    try:
        response = await client.send_message(chat_id=str(chat_id), text=safe_text)
        if response.get("ok"):
            delivery_status = "sent"
        else:
            delivery_error = str(response)
    except Exception as exc:
        delivery_error = str(exc)
        logger.error("Failed to send Telegram message: %s", exc)

    with session_scope() as session:
        msg = session.get(Message, outbound.id)
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


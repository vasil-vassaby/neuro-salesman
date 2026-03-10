import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import uuid4

import httpx

from .db import session_scope
from .models import Conversation
from .telegram_bot import handle_telegram_update


API_BASE_URL = "http://localhost:8000/api"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def _check_health_and_config(client: httpx.AsyncClient) -> None:
    response = await client.get(f"{API_BASE_URL}/health")
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError("Health check failed: ok != true")

    response = await client.get(f"{API_BASE_URL}/config")
    response.raise_for_status()
    cfg = response.json()
    required_keys = (
        "app_url",
        "web_url",
        "rag_enabled",
        "telegram_mode",
        "reminder_hours_before",
    )
    missing = [key for key in required_keys if key not in cfg]
    if missing:
        raise RuntimeError(f"/api/config missing keys: {missing}")


async def _check_booking_flow(client: httpx.AsyncClient) -> None:
    starts_at = _now_utc() + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=1)
    slot_payload: Dict[str, Any] = {
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "capacity": 1,
        "notes": "smoke test slot",
    }
    response = await client.post(f"{API_BASE_URL}/slots", json=slot_payload)
    response.raise_for_status()
    slot = response.json()
    slot_id = slot["id"]

    booking_payload: Dict[str, Any] = {
        "name": "Smoke Test",
        "phone": "+70000000000",
        "message": "Smoke test booking",
        "slot_id": slot_id,
    }
    response = await client.post(
        f"{API_BASE_URL}/web/bookings",
        json=booking_payload,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError("Web booking creation failed: ok != true")
    booking = data.get("booking") or {}
    booking_id = booking.get("id")
    if not booking_id:
        raise RuntimeError("Web booking creation failed: no booking id")

    response = await client.patch(
        f"{API_BASE_URL}/bookings/{booking_id}",
        json={"status": "confirmed"},
    )
    response.raise_for_status()

    response = await client.patch(
        f"{API_BASE_URL}/bookings/{booking_id}",
        json={"status": "cancelled", "cancel_reason": "smoke test"},
    )
    response.raise_for_status()

    response = await client.get(f"{API_BASE_URL}/slots")
    response.raise_for_status()
    slots = response.json()
    matched = [item for item in slots if item.get("id") == slot_id]
    if not matched:
        raise RuntimeError("Smoke slot not found after booking flow")
    slot_after = matched[0]
    if slot_after.get("reserved_count") != 0:
        raise RuntimeError(
            f"Slot reserved_count expected 0, "
            f"got {slot_after.get('reserved_count')}",
        )


class _FakeTelegramClient:
    def __init__(self) -> None:
        self.sent_messages: list[Dict[str, Any]] = []
        self.answered_callbacks: list[str] = []

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self.sent_messages.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
            },
        )
        return {"ok": True}

    async def answer_callback_query(self, callback_query_id: str) -> Dict[str, Any]:
        self.answered_callbacks.append(callback_query_id)
        return {"ok": True}


async def _check_telegram_text_flows() -> None:
    fake_client = _FakeTelegramClient()
    user_id = int(uuid4().int % 1_000_000_000)
    chat_id = int(uuid4().int % 1_000_000_000)

    start_update: Dict[str, Any] = {
        "update_id": int(uuid4().int % 1_000_000_000),
        "message": {
            "message_id": 1,
            "from": {
                "id": user_id,
                "first_name": "Smoke",
            },
            "chat": {
                "id": chat_id,
                "type": "private",
            },
            "text": "/start",
        },
    }
    await handle_telegram_update(start_update, fake_client)

    with session_scope() as session:
        conversation = (
            session.query(Conversation)
            .filter(
                Conversation.channel == "telegram",
                Conversation.external_user_id == str(user_id),
            )
            .first()
        )
        if conversation is None:
            raise RuntimeError("Telegram conversation was not created on /start")
        state = conversation.state or {}
        if not state.get("pd_consent", False):
            raise RuntimeError(
                f"Expected pd_consent flag in state after /start, got: {state}",
            )

    price_update: Dict[str, Any] = {
        "update_id": int(uuid4().int % 1_000_000_000),
        "message": {
            "message_id": 2,
            "from": {
                "id": user_id,
                "first_name": "Smoke",
            },
            "chat": {
                "id": chat_id,
                "type": "private",
            },
            "text": "Цена",
        },
    }
    await handle_telegram_update(price_update, fake_client)

    if not fake_client.sent_messages:
        raise RuntimeError("No Telegram replies were sent in smoke test")
    last_text = fake_client.sent_messages[-1]["text"]
    if "стоимости" not in last_text and "цена" not in last_text.lower():
        raise RuntimeError(
            "Price flow reply does not look like a price answer",
        )


async def main() -> None:
    async with httpx.AsyncClient(timeout=15.0) as client:
        await _check_health_and_config(client)
        await _check_booking_flow(client)
    await _check_telegram_text_flows()
    print("Backend smoke tests passed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # pragma: no cover - manual smoke script
        print(f"Backend smoke tests failed: {exc}", file=sys.stderr)
        sys.exit(1)


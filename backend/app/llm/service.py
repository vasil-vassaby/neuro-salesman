import logging
from typing import Any, Mapping, Optional

import httpx

from ..config import settings


logger = logging.getLogger(__name__)


def _build_system_prompt() -> str:
    """Return system prompt for safe Russian-only replies."""

    base = (
        "Ты — помощник клиники, который отвечает клиентам в чате. "
        "Отвечай только на русском языке, вежливо и простым "
        "человеческим языком.\n\n"
        "Нельзя придумывать или дополнять из головы:\n"
        "- конкретные цены или диапазоны цен, если их нет в контексте;\n"
        "- список услуг, форматы услуг или длительность, "
        "если их нет в контексте;\n"
        "- диагнозы, схемы лечения и любые медицинские "
        "рекомендации.\n\n"
        "Если информации в контексте не хватает, прямо так и скажи, "
        "что нужна дополнительная информация от специалиста или "
        "администратора, и предложи оставить заявку через "
        "веб-форму."
    )
    web_note = ""
    if settings.web_url:
        web_note = (
            "\n\nЕсли уместно, можешь добавить одну фразу с "
            "приглашением оставить заявку по ссылке: "
            f"{settings.web_url}."
        )
    return base + web_note


def _serialize_context(context: Mapping[str, Any]) -> str:
    if not context:
        return "(контекст пустой)"
    parts: list[str] = []
    for key, value in context.items():
        safe_key = str(key)
        try:
            text = str(value)
        except Exception:
            text = "(не удалось отобразить значение)"
        parts.append(f"{safe_key}: {text}")
    return "\n".join(parts)


def generate_ai_reply(
    context: Optional[Mapping[str, Any]],
    user_message: str,
) -> Optional[str]:
    """Generate safe AI reply using OpenAI-compatible chat API.

    The function respects project-wide safety constraints and returns
    ``None`` if LLM is disabled or unavailable.
    """

    if not settings.llm_enabled:
        return None
    if not settings.openai_api_key:
        logger.warning("LLM is enabled but OPENAI_API_KEY is not set.")
        return None

    serialized_context = _serialize_context(context or {})

    system_prompt = _build_system_prompt()
    payload = {
        "model": settings.openai_chat_model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": (
                    "Сообщение клиента: "
                    f"{user_message}\n\n"
                    "Контекст для ответа "
                    "(нельзя выходить за его рамки):\n"
                    f"{serialized_context}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
    }

    try:
        with httpx.Client(
            base_url=settings.openai_base_url,
            timeout=30.0,
        ) as client:
            response = client.post(
                "/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.error("Failed to call LLM chat API: %s", exc)
        return None

    try:
        choices = data.get("choices") or []
        if not choices:
            logger.warning("LLM chat API returned no choices.")
            return None
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
    except Exception as exc:
        logger.error("Failed to parse LLM response: %s", exc)
        return None

    content = content.strip()
    if not content:
        return None

    return content


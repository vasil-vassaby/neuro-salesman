import logging
from typing import Any, Mapping, Optional

from .service import generate_ai_reply


logger = logging.getLogger(__name__)


def _build_telegram_context(
    base_context: Optional[Mapping[str, Any]],
) -> Mapping[str, Any]:
    context: dict[str, Any] = {}
    if base_context:
        context.update(base_context)
    context.setdefault("channel", "telegram")
    context.setdefault("source", "telegram_bot")
    return context


def generate_assistant_reply(
    context: Optional[Mapping[str, Any]],
    user_message: str,
) -> Optional[str]:
    safe_context = _build_telegram_context(context)
    reply = generate_ai_reply(safe_context, user_message)
    if reply is None:
        logger.info(
            "Telegram assistant LLM fallback returned no reply "
            "(context_keys=%s).",
            list(safe_context.keys()),
        )
    return reply


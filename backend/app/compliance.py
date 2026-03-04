import logging
from typing import Dict

from .bootstrap import COMPLIANCE_RULES


logger = logging.getLogger(__name__)


def apply_compliance_guard(text: str) -> str:
    rules: Dict[str, object] = COMPLIANCE_RULES or {}
    banned = [phrase.lower() for phrase in rules.get("banned_phrases", [])]
    safe_text = text
    for phrase in banned:
        if not phrase:
            continue
        if phrase in safe_text.lower():
            logger.warning("Removing banned phrase from auto-reply: %s", phrase)
            safe_text = safe_text.lower().replace(phrase, "")
    high_actions = rules.get("actions", {}).get("high")
    if high_actions:
        disclaimer = rules.get("disclaimer") or ""
        if disclaimer and disclaimer not in safe_text:
            safe_text = f"{safe_text}\n\n{disclaimer}"
    return safe_text.strip()


from __future__ import annotations

from typing import Protocol


class ConsentService(Protocol):
    """Interface for personal data consent handling in Core v2."""

    def has_consent(self, conversation_id: str) -> bool:
        """Return whether consent is already recorded."""

        raise NotImplementedError

    def accept_consent(self, conversation_id: str) -> None:
        """Record consent for the given conversation."""

        raise NotImplementedError


__all__ = ["ConsentService"]


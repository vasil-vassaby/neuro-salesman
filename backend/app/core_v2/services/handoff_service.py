from __future__ import annotations

from typing import Protocol


class HandoffService(Protocol):
    """Interface for handoff mode control in Core v2."""

    def enable_handoff(self, conversation_id: str) -> None:
        """Enable manual handoff mode for a conversation."""

        raise NotImplementedError

    def disable_handoff(self, conversation_id: str) -> None:
        """Disable manual handoff mode for a conversation."""

        raise NotImplementedError

    def is_handoff_enabled(self, conversation_id: str) -> bool:
        """Return whether handoff mode is enabled."""

        raise NotImplementedError


__all__ = ["HandoffService"]


"""Transport-level abstraction for DBV-300-SD integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod


class DBV300Transport(ABC):
    """Byte-transport abstraction below the validator protocol layer."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the transport instance name."""

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Return whether the transport is currently open."""

    @abstractmethod
    async def open(self) -> None:
        """Acquire transport resources."""

    @abstractmethod
    async def close(self) -> None:
        """Release transport resources."""

    @abstractmethod
    async def write(self, payload: bytes) -> None:
        """Write raw bytes to the device transport."""

    @abstractmethod
    async def read(self, size: int = 1) -> bytes:
        """Read raw bytes from the device transport."""

    @abstractmethod
    async def flush_input(self) -> None:
        """Discard unread input buffered by the transport if supported."""

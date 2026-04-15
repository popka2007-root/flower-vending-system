"""Asynchronous command bus."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar


CommandT = TypeVar("CommandT")
CommandHandler = Callable[[Any], Awaitable[Any]]


class CommandBus:
    def __init__(self) -> None:
        self._handlers: dict[type[Any], CommandHandler] = {}

    def register_handler(self, command_type: type[Any], handler: CommandHandler) -> None:
        self._handlers[command_type] = handler

    async def dispatch(self, command: CommandT) -> Any:
        command_type = type(command)
        if command_type not in self._handlers:
            raise LookupError(f"no handler registered for command type {command_type.__name__}")
        return await self._handlers[command_type](command)

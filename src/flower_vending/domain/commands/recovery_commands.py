"""Recovery command models."""

from __future__ import annotations

from dataclasses import dataclass

from flower_vending.domain.commands import Command


@dataclass(frozen=True, slots=True)
class RecoverInterruptedTransaction(Command):
    transaction_id: str

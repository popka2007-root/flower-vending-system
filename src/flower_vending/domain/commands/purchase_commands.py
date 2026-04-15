"""Customer-flow command models."""

from __future__ import annotations

from dataclasses import dataclass

from flower_vending.domain.commands import Command


@dataclass(frozen=True, slots=True)
class StartPurchase(Command):
    product_id: str
    slot_id: str
    price_minor_units: int
    currency: str = "RUB"


@dataclass(frozen=True, slots=True)
class AcceptCash(Command):
    transaction_id: str


@dataclass(frozen=True, slots=True)
class CancelPurchase(Command):
    transaction_id: str
    reason: str = "user_cancelled"


@dataclass(frozen=True, slots=True)
class CompletePayment(Command):
    transaction_id: str


@dataclass(frozen=True, slots=True)
class DispenseChange(Command):
    transaction_id: str


@dataclass(frozen=True, slots=True)
class DispenseProduct(Command):
    transaction_id: str


@dataclass(frozen=True, slots=True)
class OpenDeliveryWindow(Command):
    transaction_id: str


@dataclass(frozen=True, slots=True)
class ConfirmPickup(Command):
    transaction_id: str

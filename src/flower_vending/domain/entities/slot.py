"""Slot entity."""

from __future__ import annotations

from dataclasses import dataclass

from flower_vending.domain.exceptions import ProductUnavailableError, SlotUnavailableError
from flower_vending.domain.value_objects import ProductId, SlotId


@dataclass(slots=True)
class Slot:
    slot_id: SlotId
    product_id: ProductId
    capacity: int
    quantity: int
    sensor_state: str = "unknown"
    is_enabled: bool = True
    last_reconciled_at: str | None = None

    def ensure_sellable(self) -> None:
        if not self.is_enabled:
            raise SlotUnavailableError(f"slot {self.slot_id.value} is disabled")
        if self.quantity <= 0:
            raise ProductUnavailableError(f"slot {self.slot_id.value} is empty")

    def decrement(self) -> None:
        self.ensure_sellable()
        self.quantity -= 1

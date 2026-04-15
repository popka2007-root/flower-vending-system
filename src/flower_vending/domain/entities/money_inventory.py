"""Money inventory entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from flower_vending.domain.entities.change_reserve import ChangeReserve
from flower_vending.domain.exceptions import ChangeUnavailableError
from flower_vending.domain.value_objects import Currency


@dataclass(slots=True)
class MoneyInventory:
    currency: Currency = field(default_factory=Currency)
    accounting_counts_by_denomination: dict[int, int] = field(default_factory=dict)
    reserved_counts_by_denomination: dict[int, int] = field(default_factory=dict)
    physical_state_confidence: float = 1.0
    exact_change_only: bool = False
    last_reconciled_at: str | None = None
    drift_detected: bool = False

    def available_counts(self) -> dict[int, int]:
        available: dict[int, int] = {}
        for denomination, count in self.accounting_counts_by_denomination.items():
            reserved = self.reserved_counts_by_denomination.get(denomination, 0)
            available[denomination] = max(0, count - reserved)
        return available

    def can_reserve(self, plan: dict[int, int]) -> bool:
        available = self.available_counts()
        return all(available.get(denomination, 0) >= count for denomination, count in plan.items())

    def reserve(self, transaction_id: str, plan: dict[int, int]) -> ChangeReserve:
        if not self.can_reserve(plan):
            raise ChangeUnavailableError("insufficient change inventory for requested reserve")
        for denomination, count in plan.items():
            self.reserved_counts_by_denomination[denomination] = (
                self.reserved_counts_by_denomination.get(denomination, 0) + count
            )
        return ChangeReserve(
            transaction_id=transaction_id,
            reserved_counts_by_denomination=dict(plan),
            currency=self.currency,
        )

    def release(self, reserve: ChangeReserve) -> None:
        for denomination, count in reserve.reserved_counts_by_denomination.items():
            current = self.reserved_counts_by_denomination.get(denomination, 0)
            self.reserved_counts_by_denomination[denomination] = max(0, current - count)
        reserve.release()

    def consume(self, reserve: ChangeReserve) -> None:
        for denomination, count in reserve.reserved_counts_by_denomination.items():
            self.accounting_counts_by_denomination[denomination] = (
                self.accounting_counts_by_denomination.get(denomination, 0) - count
            )
            self.reserved_counts_by_denomination[denomination] = max(
                0, self.reserved_counts_by_denomination.get(denomination, 0) - count
            )
        reserve.consume()

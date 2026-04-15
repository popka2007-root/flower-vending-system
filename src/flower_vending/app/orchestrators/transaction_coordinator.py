"""Transaction registry and coordination helper."""

from __future__ import annotations

from flower_vending.domain.entities import RecoveryStatus, Transaction, TransactionStatus
from flower_vending.domain.exceptions import ConcurrencyConflictError
from flower_vending.domain.value_objects import (
    Amount,
    CorrelationId,
    Currency,
    ProductId,
    SlotId,
    TransactionId,
)


class TransactionCoordinator:
    def __init__(self) -> None:
        self._transactions: dict[str, Transaction] = {}
        self._active_transaction_id: str | None = None

    def create_transaction(
        self,
        *,
        correlation_id: str,
        product_id: str,
        slot_id: str,
        price_minor_units: int,
        currency: str = "RUB",
    ) -> Transaction:
        if self._active_transaction_id is not None:
            raise ConcurrencyConflictError("a transaction is already active")
        transaction = Transaction(
            transaction_id=TransactionId.new(),
            correlation_id=CorrelationId(correlation_id),
            product_id=ProductId(product_id),
            slot_id=SlotId(slot_id),
            price=Amount(price_minor_units, Currency(currency)),
        )
        self._transactions[transaction.transaction_id.value] = transaction
        self._active_transaction_id = transaction.transaction_id.value
        return transaction

    def get(self, transaction_id: str) -> Transaction | None:
        return self._transactions.get(transaction_id)

    def require(self, transaction_id: str) -> Transaction:
        transaction = self.get(transaction_id)
        if transaction is None:
            raise KeyError(f"unknown transaction: {transaction_id}")
        return transaction

    def active(self) -> Transaction | None:
        if self._active_transaction_id is None:
            return None
        return self._transactions.get(self._active_transaction_id)

    def restore_transactions(
        self,
        transactions: list[Transaction] | tuple[Transaction, ...],
        *,
        active_transaction_id: str | None = None,
    ) -> None:
        self._transactions = {
            transaction.transaction_id.value: transaction for transaction in transactions
        }
        if active_transaction_id is not None:
            self._active_transaction_id = active_transaction_id
            return
        for transaction in transactions:
            if transaction.status not in {
                TransactionStatus.COMPLETED,
                TransactionStatus.CANCELLED,
            }:
                self._active_transaction_id = transaction.transaction_id.value
                return
        self._active_transaction_id = None

    def clear_active(self, transaction_id: str) -> None:
        if self._active_transaction_id == transaction_id:
            self._active_transaction_id = None

    def unresolved_transactions(self) -> list[Transaction]:
        return [
            transaction
            for transaction in self._transactions.values()
            if transaction.recovery_status is not RecoveryStatus.NONE
            or transaction.status.value not in {"completed", "cancelled"}
        ]

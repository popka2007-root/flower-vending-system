"""Purchase transaction aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from flower_vending.domain.entities import PaymentSession, Transaction


@dataclass(slots=True)
class PurchaseTransactionAggregate:
    transaction: Transaction

    def start_cash_session(self) -> PaymentSession:
        session = PaymentSession(transaction_id=self.transaction.transaction_id.value)
        session.start_acceptance()
        self.transaction.attach_payment_session(session)
        return session

from __future__ import annotations

import unittest
from collections.abc import Callable

from tests._support import make_temp_simulator_runtime, workspace_temp_dir

from flower_vending.app.fsm import MachineState
from flower_vending.domain.commands.purchase_commands import StartPurchase
from flower_vending.domain.entities import (
    DeliveryStatus,
    DispenseStatus,
    PaymentSession,
    PaymentStatus,
    PayoutStatus,
    RecoveryStatus,
    Transaction,
    TransactionStatus,
)
from flower_vending.domain.value_objects import Amount
from flower_vending.runtime.bootstrap import SimulatorRuntimeEnvironment


CrashSeeder = Callable[[SimulatorRuntimeEnvironment, Transaction], None]
RestartAssertion = Callable[[SimulatorRuntimeEnvironment, str], None]


class RestartCrashWindowRecoveryTests(unittest.IsolatedAsyncioTestCase):
    # These tests persist the exact crash window, restart the runtime, and assert sales stay blocked.

    async def test_restart_after_cash_accepted_payment_not_complete_blocks_sales(self) -> None:
        await self._assert_restart_requires_recovery(self._seed_cash_accepted_payment_not_complete)

    async def test_restart_after_payment_confirmed_change_pending_blocks_sales(self) -> None:
        await self._assert_restart_requires_recovery(self._seed_payment_confirmed_change_pending)

    async def test_restart_after_change_intent_without_outcome_requires_manual_review(self) -> None:
        await self._assert_restart_requires_recovery(
            self._seed_change_intent_without_outcome,
            self._assert_manual_review_transaction,
        )

    async def test_restart_after_vend_motor_intent_without_outcome_requires_manual_review(self) -> None:
        await self._assert_restart_requires_recovery(
            self._seed_vend_motor_intent_without_outcome,
            self._assert_manual_review_transaction,
        )

    async def test_restart_after_window_opened_pickup_not_confirmed_blocks_sales(self) -> None:
        await self._assert_restart_requires_recovery(self._seed_window_opened_pickup_not_confirmed)

    async def test_restart_with_recovery_pending_transaction_blocks_sales(self) -> None:
        await self._assert_restart_requires_recovery(
            self._seed_recovery_pending_transaction,
            self._assert_recovery_pending_transaction,
        )

    async def _assert_restart_requires_recovery(
        self,
        seed_crash_window: CrashSeeder,
        extra_assertion: RestartAssertion | None = None,
    ) -> None:
        with workspace_temp_dir(prefix="restart-crash-") as tmp:
            runtime = make_temp_simulator_runtime(tmp)
            environment = await runtime.build()
            await environment.start()
            try:
                transaction_id = await self._start_persisted_transaction(environment)
                transaction = environment.core.transaction_coordinator.require(transaction_id)
                seed_crash_window(environment, transaction)
                transaction.touch()
                environment.repositories.transactions.save(transaction)
            finally:
                await environment.stop()

            restarted = await runtime.build()
            await restarted.start()
            try:
                self._assert_safe_recovery_state(restarted, transaction_id)
                if extra_assertion is not None:
                    extra_assertion(restarted, transaction_id)
            finally:
                await restarted.stop()

    async def _start_persisted_transaction(self, environment: SimulatorRuntimeEnvironment) -> str:
        item = environment.config.catalog.items[0]
        transaction_id = await environment.core.command_bus.dispatch(
            StartPurchase(
                correlation_id="restart-crash-window",
                product_id=item.product_id,
                slot_id=item.slot_id,
                price_minor_units=item.price_minor_units,
                currency=environment.config.machine.currency,
            )
        )
        transaction = environment.core.transaction_coordinator.require(transaction_id)
        environment.repositories.transactions.save(transaction)
        return transaction_id

    def _seed_cash_accepted_payment_not_complete(
        self,
        _environment: SimulatorRuntimeEnvironment,
        transaction: Transaction,
    ) -> None:
        session = PaymentSession(transaction_id=transaction.transaction_id.value)
        session.start_acceptance()
        session.add_stacked_bill(100)
        transaction.attach_payment_session(session)
        transaction.accepted_amount = session.accepted_amount
        transaction.status = TransactionStatus.ACCEPTING_CASH
        transaction.payment_status = PaymentStatus.ACCEPTING

    def _seed_payment_confirmed_change_pending(
        self,
        _environment: SimulatorRuntimeEnvironment,
        transaction: Transaction,
    ) -> None:
        currency = transaction.price.currency
        transaction.accepted_amount = Amount(transaction.price.minor_units + 100, currency)
        transaction.change_due = Amount(100, currency)
        transaction.status = TransactionStatus.DISPENSING_CHANGE
        transaction.payment_status = PaymentStatus.CONFIRMED
        transaction.payout_status = PayoutStatus.PENDING

    def _seed_change_intent_without_outcome(
        self,
        environment: SimulatorRuntimeEnvironment,
        transaction: Transaction,
    ) -> None:
        self._seed_payment_confirmed_change_pending(environment, transaction)
        environment.repositories.journal.record_intent(
            action_name="change_dispense_requested",
            correlation_id=transaction.correlation_id.value,
            transaction_id=transaction.transaction_id.value,
            logical_step="complete_payment.dispense_change",
            machine_state=MachineState.DISPENSING_CHANGE.value,
            transaction_status=transaction.status.value,
            payload={"change_due_minor_units": transaction.change_due.minor_units},
        )

    def _seed_vend_motor_intent_without_outcome(
        self,
        environment: SimulatorRuntimeEnvironment,
        transaction: Transaction,
    ) -> None:
        transaction.accepted_amount = transaction.price
        transaction.change_due = Amount(0, transaction.price.currency)
        transaction.status = TransactionStatus.DISPENSING_PRODUCT
        transaction.payment_status = PaymentStatus.CONFIRMED
        transaction.payout_status = PayoutStatus.NOT_REQUIRED
        transaction.dispense_status = DispenseStatus.AUTHORIZED
        environment.repositories.journal.record_intent(
            action_name="motor_vend_requested",
            correlation_id=transaction.correlation_id.value,
            transaction_id=transaction.transaction_id.value,
            logical_step="handle_vend_authorized.vend_motor",
            machine_state=MachineState.DISPENSING_PRODUCT.value,
            transaction_status=transaction.status.value,
            payload={"slot_id": transaction.slot_id.value},
        )

    def _seed_window_opened_pickup_not_confirmed(
        self,
        _environment: SimulatorRuntimeEnvironment,
        transaction: Transaction,
    ) -> None:
        transaction.accepted_amount = transaction.price
        transaction.change_due = Amount(0, transaction.price.currency)
        transaction.status = TransactionStatus.WAITING_FOR_CUSTOMER_PICKUP
        transaction.payment_status = PaymentStatus.CONFIRMED
        transaction.payout_status = PayoutStatus.NOT_REQUIRED
        transaction.dispense_status = DispenseStatus.DISPENSED
        transaction.delivery_status = DeliveryStatus.WINDOW_OPENED

    def _seed_recovery_pending_transaction(
        self,
        _environment: SimulatorRuntimeEnvironment,
        transaction: Transaction,
    ) -> None:
        transaction.accepted_amount = transaction.price
        transaction.change_due = Amount(0, transaction.price.currency)
        transaction.status = TransactionStatus.AMBIGUOUS
        transaction.payment_status = PaymentStatus.CONFIRMED
        transaction.recovery_status = RecoveryStatus.PENDING

    def _assert_safe_recovery_state(
        self,
        environment: SimulatorRuntimeEnvironment,
        transaction_id: str,
    ) -> None:
        report = environment.diagnostics_report()
        machine = report["machine"]
        self.assertIn(
            machine["machine_state"],
            {MachineState.RECOVERY_PENDING.value, MachineState.OUT_OF_SERVICE.value},
        )
        self.assertIn("recovery_pending", machine["sale_blockers"])
        self.assertEqual(machine["active_transaction_id"], transaction_id)
        self.assertIn(transaction_id, report["unresolved_transaction_ids"])
        self.assertFalse(machine["allow_cash_sales"])
        self.assertFalse(machine["allow_vending"])

    def _assert_manual_review_transaction(
        self,
        environment: SimulatorRuntimeEnvironment,
        transaction_id: str,
    ) -> None:
        transaction = environment.core.transaction_coordinator.require(transaction_id)
        self.assertEqual(transaction.status, TransactionStatus.AMBIGUOUS)
        self.assertEqual(transaction.recovery_status, RecoveryStatus.MANUAL_REVIEW)
        self.assertEqual(len(environment.repositories.journal.unresolved_intents()), 1)

    def _assert_recovery_pending_transaction(
        self,
        environment: SimulatorRuntimeEnvironment,
        transaction_id: str,
    ) -> None:
        transaction = environment.core.transaction_coordinator.require(transaction_id)
        self.assertEqual(transaction.recovery_status, RecoveryStatus.PENDING)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from _support import workspace_temp_dir

from flower_vending.domain.entities import TransactionStatus
from flower_vending.domain.events.payment_events import payment_event
from flower_vending.infrastructure.persistence.journal import SQLiteTransactionJournal
from flower_vending.infrastructure.persistence.sqlite import SQLiteDatabase, TransactionRepository, ensure_sqlite_schema
from flower_vending.simulators.faults import SimulatorFaultCode
from flower_vending.simulators.harness import SimulationHarness


class RecoveryAndPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_reboot_mid_transaction_leaves_durable_recovery_evidence(self) -> None:
        with workspace_temp_dir(prefix="recovery-") as tmp:
            db_path = tmp / "recovery.db"

            harness = SimulationHarness.build()
            await harness.start()
            try:
                transaction_id = await harness.start_purchase(correlation_id="reboot-mid-transaction")
                transaction = harness.core.transaction_coordinator.require(transaction_id)
                transaction.status = TransactionStatus.WAITING_FOR_PAYMENT

                db = SQLiteDatabase(db_path)
                try:
                    ensure_sqlite_schema(db)
                    transaction_repo = TransactionRepository(db)
                    journal = SQLiteTransactionJournal(db)
                    transaction_repo.save(transaction)
                    journal.append_intent(
                        intent_name="start_purchase",
                        correlation_id="reboot-mid-transaction",
                        transaction_id=transaction_id,
                        machine_state="WAITING_FOR_PAYMENT",
                        transaction_status=transaction.status.value,
                        product_id=transaction.product_id.value,
                        slot_id=transaction.slot_id.value,
                    )
                    journal.append_event(
                        payment_event(
                            "purchase_started",
                            correlation_id="reboot-mid-transaction",
                            transaction_id=transaction_id,
                            product_id=transaction.product_id.value,
                            slot_id=transaction.slot_id.value,
                        ),
                        machine_state="WAITING_FOR_PAYMENT",
                        transaction_status=transaction.status.value,
                    )
                finally:
                    db.close()
            finally:
                await harness.stop()

            rebooted_db = SQLiteDatabase(db_path)
            try:
                transaction_repo = TransactionRepository(rebooted_db)
                journal = SQLiteTransactionJournal(rebooted_db)
                loaded_transaction = transaction_repo.get(transaction_id)
                self.assertIsNotNone(loaded_transaction)
                self.assertEqual(loaded_transaction.status.value, "waiting_for_payment")
                self.assertIn(transaction_id, journal.unresolved_transaction_ids())
                self.assertEqual(len(journal.read_for_transaction(transaction_id)), 2)
            finally:
                rebooted_db.close()

    async def test_recovery_manager_marks_partial_payout_for_manual_review(self) -> None:
        harness = SimulationHarness.build(
            price_minor_units=300,
            change_inventory={100: 2},
            accepted_bill_denominations=(500,),
        )
        await harness.start()
        try:
            transaction_id = await harness.start_purchase(correlation_id="recovery-partial")
            await harness.accept_cash(transaction_id, correlation_id="recovery-partial")
            harness.change_dispenser.inject_fault(
                SimulatorFaultCode.PARTIAL_PAYOUT,
                message="simulated partial payout",
            )
            with self.assertRaises(Exception):
                await harness.insert_bill(500, correlation_id="recovery-partial")

            transaction = harness.core.transaction_coordinator.require(transaction_id)
            plan = harness.core.recovery_manager.assess(transaction)
            self.assertEqual(plan.action, "manual_review")
            self.assertTrue(plan.operator_required)
            self.assertEqual(plan.reason, "ambiguous_side_effect")
        finally:
            await harness.stop()

if __name__ == "__main__":
    unittest.main()

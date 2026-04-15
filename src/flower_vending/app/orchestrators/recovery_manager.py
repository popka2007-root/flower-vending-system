"""Recovery orchestration for unresolved transactions."""

from __future__ import annotations

from dataclasses import dataclass

from flower_vending.app.event_bus import EventBus
from flower_vending.app.fsm import MachineState, StateMachineEngine
from flower_vending.app.orchestrators.transaction_coordinator import TransactionCoordinator
from flower_vending.app.services.machine_status_service import MachineStatusService
from flower_vending.domain.entities import PaymentStatus, PayoutStatus, Transaction, TransactionStatus
from flower_vending.domain.events.machine_events import machine_event
from flower_vending.domain.exceptions import ManualInterventionRequiredError


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    transaction_id: str
    action: str
    reason: str
    operator_required: bool


class RecoveryManager:
    def __init__(
        self,
        *,
        transaction_coordinator: TransactionCoordinator,
        event_bus: EventBus,
        fsm: StateMachineEngine,
        machine_status_service: MachineStatusService,
    ) -> None:
        self._transaction_coordinator = transaction_coordinator
        self._event_bus = event_bus
        self._fsm = fsm
        self._machine_status_service = machine_status_service

    def assess(self, transaction: Transaction) -> RecoveryPlan:
        if transaction.status in {TransactionStatus.COMPLETED, TransactionStatus.CANCELLED}:
            return RecoveryPlan(transaction.transaction_id.value, "none", "transaction_terminal", False)
        if transaction.status in {TransactionStatus.AMBIGUOUS, TransactionStatus.FAULTED}:
            return RecoveryPlan(transaction.transaction_id.value, "manual_review", "ambiguous_side_effect", True)
        if transaction.payment_status is PaymentStatus.CONFIRMED and transaction.payout_status in {
            PayoutStatus.PARTIAL,
            PayoutStatus.AMBIGUOUS,
            PayoutStatus.FAILED,
        }:
            return RecoveryPlan(transaction.transaction_id.value, "manual_review", "payout_unresolved", True)
        if transaction.payment_status is PaymentStatus.CONFIRMED:
            return RecoveryPlan(transaction.transaction_id.value, "pending_review", "confirmed_payment_replay_needed", True)
        return RecoveryPlan(transaction.transaction_id.value, "cancel_safe", "payment_not_confirmed", False)

    async def recover_transaction(self, transaction_id: str, correlation_id: str) -> RecoveryPlan:
        transaction = self._transaction_coordinator.require(transaction_id)
        plan = self.assess(transaction)
        if self._fsm.can_transition(MachineState.RECOVERY_PENDING):
            self._fsm.transition(MachineState.RECOVERY_PENDING, "recovery_started")
        else:
            self._fsm.force_state(MachineState.RECOVERY_PENDING, "recovery_started_forced")
        self._machine_status_service.set_machine_state(self._fsm.current_state)
        self._machine_status_service.block_sales("recovery_pending")
        await self._event_bus.publish(
            machine_event(
                "recovery_started",
                correlation_id=correlation_id,
                transaction_id=transaction_id,
                action=plan.action,
                reason=plan.reason,
            )
        )
        if plan.operator_required:
            await self._event_bus.publish(
                machine_event(
                    "manual_review_required",
                    correlation_id=correlation_id,
                    transaction_id=transaction_id,
                    action=plan.action,
                    reason=plan.reason,
                )
            )
            raise ManualInterventionRequiredError(plan.reason)
        if plan.action == "cancel_safe":
            transaction.cancel()
            self._transaction_coordinator.clear_active(transaction_id)
            self._machine_status_service.set_active_transaction(None)
            self._machine_status_service.unblock_sales("recovery_pending")
            self._fsm.transition(MachineState.IDLE, "recovery_completed")
            self._machine_status_service.set_machine_state(self._fsm.current_state)
            await self._event_bus.publish(
                machine_event(
                    "recovery_completed",
                    correlation_id=correlation_id,
                    transaction_id=transaction_id,
                    action=plan.action,
                )
            )
        return plan

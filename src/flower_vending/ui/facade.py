"""Application-facing facade used by the UI presenter layer."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from flower_vending.app import ApplicationCore
from flower_vending.app.fsm import MachineState
from flower_vending.domain.commands.purchase_commands import AcceptCash, CancelPurchase, ConfirmPickup, StartPurchase
from flower_vending.domain.commands.recovery_commands import RecoverInterruptedTransaction
from flower_vending.domain.commands.service_commands import EnterServiceMode
from flower_vending.domain.entities import Product, Slot, Transaction
from flower_vending.domain.events import DomainEvent
from flower_vending.domain.value_objects import CorrelationId
from flower_vending.platform.common import PlatformProfile
from flower_vending.simulators.control import EventLogEntry, RecentEventStore, SimulatorControlService


EventListener = Callable[[DomainEvent], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    product_id: str
    slot_id: str
    display_name: str
    category: str
    price_minor_units: int
    currency_code: str
    quantity: int
    available: bool
    is_bouquet: bool
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class MachineUiSnapshot:
    machine_state: str
    exact_change_only: bool
    sale_blockers: tuple[str, ...]
    allow_cash_sales: bool
    allow_vending: bool
    service_mode: bool
    active_transaction_id: str | None


@dataclass(frozen=True, slots=True)
class TransactionUiSnapshot:
    transaction_id: str
    product_id: str
    slot_id: str
    product_name: str
    price_minor_units: int
    currency_code: str
    accepted_minor_units: int
    change_due_minor_units: int
    status: str
    payment_status: str
    payout_status: str
    pickup_timeout_active: bool = False
    pickup_timeout_remaining_s: float | None = None


@dataclass(frozen=True, slots=True)
class DeviceDiagnosticsRow:
    device_name: str
    state: str
    fault_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiagnosticsSnapshot:
    machine: MachineUiSnapshot
    devices: tuple[DeviceDiagnosticsRow, ...]
    unresolved_transaction_ids: tuple[str, ...]
    recent_events: tuple[EventLogEntry, ...] = ()


class UiApplicationFacade:
    """Expose application-layer operations to presenters without leaking Qt into core."""

    def __init__(
        self,
        core: ApplicationCore,
        *,
        event_store: RecentEventStore | None = None,
        simulator_controls: SimulatorControlService | None = None,
        platform_profile: PlatformProfile | None = None,
    ) -> None:
        self._core = core
        self._event_store = event_store
        self._simulator_controls = simulator_controls
        self._platform_profile = platform_profile

    def subscribe_events(self, handler: EventListener) -> None:
        self._core.event_bus.subscribe_best_effort("*", handler)

    def new_correlation_id(self) -> str:
        return CorrelationId.new().value

    def catalog_entries(self) -> tuple[CatalogEntry, ...]:
        entries: list[CatalogEntry] = []
        for product, slot in self._core.inventory_service.list_catalog():
            entries.append(self._catalog_entry(product, slot))
        return tuple(entries)

    def get_catalog_entry(self, product_id: str, slot_id: str) -> CatalogEntry:
        product, slot = self._core.inventory_service.ensure_selection(product_id, slot_id)
        return self._catalog_entry(product, slot)

    def machine_snapshot(self) -> MachineUiSnapshot:
        status = self._core.machine_status_service.runtime.status
        return MachineUiSnapshot(
            machine_state=status.machine_state,
            exact_change_only=status.exact_change_only,
            sale_blockers=tuple(sorted(status.sale_blockers)),
            allow_cash_sales=status.allow_cash_sales,
            allow_vending=status.allow_vending,
            service_mode=status.service_mode,
            active_transaction_id=status.active_transaction_id,
        )

    def active_transaction_snapshot(self) -> TransactionUiSnapshot | None:
        transaction = self._core.transaction_coordinator.active()
        if transaction is None:
            unresolved = self._core.transaction_coordinator.unresolved_transactions()
            transaction = unresolved[-1] if unresolved else None
        if transaction is None:
            return None
        return self._transaction_snapshot(transaction)

    def diagnostics_snapshot(self) -> DiagnosticsSnapshot:
        health = self._core.health_monitor.snapshot
        devices = (
            DeviceDiagnosticsRow("validator", health.validator_state.value, tuple()),
            DeviceDiagnosticsRow("change_dispenser", health.change_dispenser_state.value, tuple()),
            DeviceDiagnosticsRow("motor", health.motor_state.value, tuple()),
            DeviceDiagnosticsRow("cooling", health.cooling_state.value, tuple()),
            DeviceDiagnosticsRow("window", health.window_state.value, tuple()),
            DeviceDiagnosticsRow("temperature", health.temperature_sensor_state.value, tuple()),
            DeviceDiagnosticsRow("door", health.door_sensor_state.value, tuple()),
            DeviceDiagnosticsRow("inventory", health.inventory_sensor_state.value, tuple()),
            DeviceDiagnosticsRow("watchdog", health.watchdog_state.value, tuple()),
        )
        unresolved_ids = tuple(
            transaction.transaction_id.value
            for transaction in self._core.transaction_coordinator.unresolved_transactions()
        )
        return DiagnosticsSnapshot(
            machine=self.machine_snapshot(),
            devices=devices,
            unresolved_transaction_ids=unresolved_ids,
            recent_events=tuple() if self._event_store is None else self._event_store.snapshot(),
        )

    def quick_insert_denominations(self) -> tuple[int, ...]:
        if self._simulator_controls is None:
            return ()
        return self._simulator_controls.quick_insert_denominations()

    def simulator_action_ids(self) -> tuple[str, ...]:
        if self._simulator_controls is None:
            return ()
        return self._simulator_controls.available_actions()

    @property
    def platform_profile(self) -> PlatformProfile | None:
        return self._platform_profile

    async def start_cash_checkout(self, *, product_id: str, slot_id: str, correlation_id: str) -> str:
        entry = self.get_catalog_entry(product_id, slot_id)
        transaction_id = await self._core.command_bus.dispatch(
            StartPurchase(
                correlation_id=correlation_id,
                product_id=product_id,
                slot_id=slot_id,
                price_minor_units=entry.price_minor_units,
                currency=entry.currency_code,
            )
        )
        await self._core.command_bus.dispatch(
            AcceptCash(correlation_id=correlation_id, transaction_id=transaction_id)
        )
        return transaction_id

    async def cancel_purchase(self, *, transaction_id: str, correlation_id: str) -> str:
        return await self._core.command_bus.dispatch(
            CancelPurchase(correlation_id=correlation_id, transaction_id=transaction_id)
        )

    async def confirm_pickup(self, *, transaction_id: str, correlation_id: str) -> str:
        return await self._core.command_bus.dispatch(
            ConfirmPickup(correlation_id=correlation_id, transaction_id=transaction_id)
        )

    async def enter_service_mode(
        self,
        *,
        operator_id: str,
        correlation_id: str,
        reason: str = "ui_service_mode_request",
    ) -> str:
        return await self._core.command_bus.dispatch(
            EnterServiceMode(
                correlation_id=correlation_id,
                operator_id=operator_id,
                reason=reason,
            )
        )

    async def exit_service_mode(
        self,
        *,
        correlation_id: str,
        operator_id: str | None = None,
    ) -> str:
        return await self._core.service_mode_coordinator.exit_service_mode(
            correlation_id=correlation_id,
            operator_id=operator_id,
        )

    async def recover_transaction(self, *, transaction_id: str, correlation_id: str) -> str:
        await self._core.command_bus.dispatch(
            RecoverInterruptedTransaction(
                correlation_id=correlation_id,
                transaction_id=transaction_id,
            )
        )
        return MachineState.RECOVERY_PENDING.value

    async def insert_simulated_bill(self, *, bill_minor_units: int, correlation_id: str) -> None:
        if self._simulator_controls is None:
            raise RuntimeError("simulator controls are not available")
        await self._simulator_controls.insert_bill(
            bill_minor_units=bill_minor_units,
            correlation_id=correlation_id,
        )

    async def execute_simulator_action(self, *, action_id: str, correlation_id: str) -> None:
        if self._simulator_controls is None:
            raise RuntimeError("simulator controls are not available")
        await self._simulator_controls.execute_action(
            action_id,
            correlation_id=correlation_id,
        )

    def _catalog_entry(self, product: Product, slot: Slot) -> CatalogEntry:
        available = product.enabled and slot.is_enabled and slot.quantity > 0
        return CatalogEntry(
            product_id=product.product_id.value,
            slot_id=slot.slot_id.value,
            display_name=product.display_name,
            category=product.category,
            price_minor_units=product.price.minor_units,
            currency_code=product.price.currency.code,
            quantity=slot.quantity,
            available=available,
            is_bouquet=product.is_bouquet,
            metadata=dict(product.metadata),
        )

    def _transaction_snapshot(self, transaction: Transaction) -> TransactionUiSnapshot:
        product = self._core.inventory_service.get_product(transaction.product_id.value)
        pickup_timeout_remaining_s = self._core.pickup_timeout_coordinator.remaining_seconds(
            transaction.transaction_id.value
        )
        return TransactionUiSnapshot(
            transaction_id=transaction.transaction_id.value,
            product_id=transaction.product_id.value,
            slot_id=transaction.slot_id.value,
            product_name=product.display_name,
            price_minor_units=transaction.price.minor_units,
            currency_code=transaction.price.currency.code,
            accepted_minor_units=transaction.accepted_amount.minor_units,
            change_due_minor_units=transaction.change_due.minor_units,
            status=transaction.status.value,
            payment_status=transaction.payment_status.value,
            payout_status=transaction.payout_status.value,
            pickup_timeout_active=pickup_timeout_remaining_s is not None,
            pickup_timeout_remaining_s=pickup_timeout_remaining_s,
        )

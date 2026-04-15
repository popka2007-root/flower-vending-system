"""Bootstrap wiring for the Phase 5 application core."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any

from flower_vending.app.command_bus import CommandBus
from flower_vending.app.event_bus import EventBus
from flower_vending.app.fsm import MachineState, StateMachineEngine
from flower_vending.app.orchestrators import (
    HealthMonitor,
    PaymentCoordinator,
    RecoveryManager,
    ServiceModeCoordinator,
    TransactionCoordinator,
    VendingController,
)
from flower_vending.app.services import InventoryService, MachineStatusService
from flower_vending.devices.contracts import BillValidatorEvent
from flower_vending.devices.interfaces import (
    BillValidator,
    ChangeDispenser,
    DoorSensor,
    InventorySensor,
    ManagedDevice,
    MotorController,
    TemperatureSensor,
    WatchdogAdapter,
    WindowController,
)
from flower_vending.domain.aggregates import MachineRuntimeAggregate
from flower_vending.domain.commands.purchase_commands import (
    AcceptCash,
    CancelPurchase,
    ConfirmPickup,
    StartPurchase,
)
from flower_vending.domain.commands.recovery_commands import RecoverInterruptedTransaction
from flower_vending.domain.commands.service_commands import EnterServiceMode
from flower_vending.domain.entities import MoneyInventory
from flower_vending.payments.change_manager import ChangeManager


@dataclass(slots=True)
class ApplicationCore:
    validator: BillValidator
    command_bus: CommandBus
    event_bus: EventBus
    fsm: StateMachineEngine
    inventory_service: InventoryService
    machine_status_service: MachineStatusService
    transaction_coordinator: TransactionCoordinator
    payment_coordinator: PaymentCoordinator
    vending_controller: VendingController
    recovery_manager: RecoveryManager
    service_mode_coordinator: ServiceModeCoordinator
    health_monitor: HealthMonitor
    watchdog: WatchdogAdapter | None = None
    health_poll_interval_s: float = 0.5
    validator_event_timeout_s: float = 0.05
    watchdog_timeout_s: float = 30.0
    _runtime_stop: asyncio.Event = field(default_factory=asyncio.Event, init=False)
    _runtime_tasks: list[asyncio.Task[None]] = field(default_factory=list, init=False)
    _runtime_failures: list[BaseException] = field(default_factory=list, init=False)

    async def process_validator_event(self, event: BillValidatorEvent) -> None:
        await self.payment_coordinator.process_validator_event(event)

    async def start_runtime(self) -> None:
        """Start application-owned background supervision loops."""
        if self._runtime_tasks:
            return
        self._runtime_stop.clear()
        self._runtime_failures.clear()
        await self.health_monitor.poll_once(correlation_id="startup-health")
        if self.watchdog is not None:
            await self.watchdog.arm(self.watchdog_timeout_s)
        self._spawn_runtime_task(self._validator_event_loop(), "validator-events")
        self._spawn_runtime_task(self._health_monitor_loop(), "health-monitor")

    async def stop_runtime(self) -> None:
        self._runtime_stop.set()
        for task in self._runtime_tasks:
            task.cancel()
        if self._runtime_tasks:
            await asyncio.gather(*self._runtime_tasks, return_exceptions=True)
        self._runtime_tasks.clear()
        if self.watchdog is not None:
            with suppress(Exception):
                await self.watchdog.disarm()

    def raise_runtime_failure(self) -> None:
        if self._runtime_failures:
            raise self._runtime_failures.pop(0)

    def _spawn_runtime_task(self, coroutine: Coroutine[Any, Any, None], name: str) -> None:
        task = asyncio.create_task(coroutine, name=f"flower-vending-{name}")
        task.add_done_callback(self._capture_runtime_failure)
        self._runtime_tasks.append(task)

    def _capture_runtime_failure(self, task: asyncio.Task[None]) -> None:
        if task.cancelled():
            return
        failure = task.exception()
        if failure is not None:
            self._runtime_failures.append(failure)

    async def _validator_event_loop(self) -> None:
        while not self._runtime_stop.is_set():
            event = await self.validator.read_event(timeout_s=self.validator_event_timeout_s)
            if event is None:
                continue
            await self.process_validator_event(event)

    async def _health_monitor_loop(self) -> None:
        while not self._runtime_stop.is_set():
            try:
                await asyncio.wait_for(
                    self._runtime_stop.wait(),
                    timeout=self.health_poll_interval_s,
                )
                break
            except asyncio.TimeoutError:
                pass
            await self.health_monitor.poll_once()
            if self.watchdog is not None:
                await self.watchdog.kick()


def build_application_core(
    *,
    validator: BillValidator,
    change_dispenser: ChangeDispenser,
    motor_controller: MotorController,
    window_controller: WindowController,
    inventory_service: InventoryService,
    money_inventory: MoneyInventory,
    devices: dict[str, ManagedDevice],
    accepted_bill_denominations: tuple[int, ...] = (),
    door_sensor: DoorSensor | None = None,
    temperature_sensor: TemperatureSensor | None = None,
    inventory_sensor: InventorySensor | None = None,
    initial_state: MachineState = MachineState.IDLE,
    critical_temperature_celsius: float = 8.0,
    health_poll_interval_s: float = 0.5,
    validator_event_timeout_s: float = 0.05,
    watchdog_timeout_s: float = 30.0,
) -> ApplicationCore:
    event_bus = EventBus()
    command_bus = CommandBus()
    fsm = StateMachineEngine(initial_state=initial_state)
    machine_status_service = MachineStatusService(MachineRuntimeAggregate())
    machine_status_service.set_machine_state(initial_state)

    transaction_coordinator = TransactionCoordinator()
    change_manager = ChangeManager(
        inventory=money_inventory,
        change_dispenser=change_dispenser,
        accepted_bill_denominations=accepted_bill_denominations,
    )
    payment_coordinator = PaymentCoordinator(
        validator=validator,
        change_manager=change_manager,
        transaction_coordinator=transaction_coordinator,
        event_bus=event_bus,
        fsm=fsm,
        machine_status_service=machine_status_service,
    )
    vending_controller = VendingController(
        inventory_service=inventory_service,
        payment_coordinator=payment_coordinator,
        transaction_coordinator=transaction_coordinator,
        motor_controller=motor_controller,
        window_controller=window_controller,
        inventory_sensor=inventory_sensor,
        event_bus=event_bus,
        fsm=fsm,
        machine_status_service=machine_status_service,
    )
    recovery_manager = RecoveryManager(
        transaction_coordinator=transaction_coordinator,
        event_bus=event_bus,
        fsm=fsm,
        machine_status_service=machine_status_service,
    )
    service_mode_coordinator = ServiceModeCoordinator(
        event_bus=event_bus,
        fsm=fsm,
        machine_status_service=machine_status_service,
    )
    health_monitor = HealthMonitor(
        devices=devices,
        machine_status_service=machine_status_service,
        event_bus=event_bus,
        door_sensor=door_sensor,
        temperature_sensor=temperature_sensor,
        critical_temperature_celsius=critical_temperature_celsius,
    )
    watchdog_device = devices.get("watchdog")
    watchdog = watchdog_device if isinstance(watchdog_device, WatchdogAdapter) else None

    command_bus.register_handler(StartPurchase, vending_controller.start_purchase)
    command_bus.register_handler(AcceptCash, vending_controller.accept_cash)
    command_bus.register_handler(CancelPurchase, vending_controller.cancel_purchase)
    command_bus.register_handler(ConfirmPickup, vending_controller.confirm_pickup)
    command_bus.register_handler(
        RecoverInterruptedTransaction,
        lambda command: recovery_manager.recover_transaction(command.transaction_id, command.correlation_id),
    )
    command_bus.register_handler(EnterServiceMode, service_mode_coordinator.enter_service_mode)
    event_bus.subscribe("vend_authorized", vending_controller.handle_vend_authorized)

    return ApplicationCore(
        validator=validator,
        command_bus=command_bus,
        event_bus=event_bus,
        fsm=fsm,
        inventory_service=inventory_service,
        machine_status_service=machine_status_service,
        transaction_coordinator=transaction_coordinator,
        payment_coordinator=payment_coordinator,
        vending_controller=vending_controller,
        recovery_manager=recovery_manager,
        service_mode_coordinator=service_mode_coordinator,
        health_monitor=health_monitor,
        watchdog=watchdog,
        health_poll_interval_s=health_poll_interval_s,
        validator_event_timeout_s=validator_event_timeout_s,
        watchdog_timeout_s=watchdog_timeout_s,
    )

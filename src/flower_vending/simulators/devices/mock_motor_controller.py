"""Deterministic mock motor controller."""

from __future__ import annotations

from flower_vending.devices.contracts import DeviceOperationalState
from flower_vending.devices.exceptions import DeviceAdapterError
from flower_vending.devices.interfaces import MotorController
from flower_vending.simulators.devices.base import MockManagedDevice
from flower_vending.simulators.faults import SimulatorFaultCode


class MockMotorController(MockManagedDevice, MotorController):
    def __init__(self, name: str = "mock_motor") -> None:
        super().__init__(name)
        self.vend_history: list[str] = []

    async def home(self, correlation_id: str | None = None) -> None:
        self._heartbeat(state=DeviceOperationalState.READY, action="home")

    async def vend_slot(self, slot_id: str, correlation_id: str | None = None) -> None:
        plan = self.injector.consume(SimulatorFaultCode.MOTOR_FAULT)
        if plan is not None:
            self._activate_fault(
                code=plan.code.value,
                message=plan.message or "motor fault",
                **plan.details,
            )
            raise DeviceAdapterError(plan.message or "motor fault")
        self.vend_history.append(slot_id)
        self._heartbeat(state=DeviceOperationalState.READY, last_slot=slot_id)

    async def stop_motion(self) -> None:
        self._heartbeat(state=DeviceOperationalState.DEGRADED, action="stop_motion")

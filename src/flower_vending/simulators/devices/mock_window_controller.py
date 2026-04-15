"""Deterministic mock delivery window controller."""

from __future__ import annotations

from flower_vending.devices.contracts import DeviceOperationalState, WindowPosition, WindowStatus
from flower_vending.devices.exceptions import DeviceAdapterError
from flower_vending.devices.interfaces import WindowController
from flower_vending.simulators.devices.base import MockManagedDevice
from flower_vending.simulators.faults import SimulatorFaultCode


class MockWindowController(MockManagedDevice, WindowController):
    def __init__(self, name: str = "mock_window_controller") -> None:
        super().__init__(name)
        self._status = WindowStatus(controller_name=name, position=WindowPosition.CLOSED, locked=False)

    async def open_window(self, correlation_id: str | None = None) -> None:
        plan = self.injector.consume(SimulatorFaultCode.WINDOW_FAULT)
        if plan is not None:
            self._activate_fault(
                code=plan.code.value,
                message=plan.message or "window fault",
                **plan.details,
            )
            raise DeviceAdapterError(plan.message or "window fault")
        self._status = WindowStatus(controller_name=self.name, position=WindowPosition.OPEN, locked=False)
        self._heartbeat(state=DeviceOperationalState.READY, position=self._status.position.value)

    async def close_window(self, correlation_id: str | None = None) -> None:
        plan = self.injector.consume(SimulatorFaultCode.WINDOW_FAULT)
        if plan is not None:
            self._activate_fault(
                code=plan.code.value,
                message=plan.message or "window fault",
                **plan.details,
            )
            raise DeviceAdapterError(plan.message or "window fault")
        self._status = WindowStatus(controller_name=self.name, position=WindowPosition.CLOSED, locked=False)
        self._heartbeat(state=DeviceOperationalState.READY, position=self._status.position.value)

    async def get_window_status(self) -> WindowStatus:
        return self._status

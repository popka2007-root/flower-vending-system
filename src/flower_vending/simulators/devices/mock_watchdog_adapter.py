"""Deterministic mock watchdog adapter."""

from __future__ import annotations

from flower_vending.devices.contracts import DeviceOperationalState
from flower_vending.devices.exceptions import DeviceAdapterError
from flower_vending.devices.interfaces import WatchdogAdapter
from flower_vending.simulators.devices.base import MockManagedDevice
from flower_vending.simulators.faults import SimulatorFaultCode


class MockWatchdogAdapter(MockManagedDevice, WatchdogAdapter):
    def __init__(self, name: str = "mock_watchdog") -> None:
        super().__init__(name)
        self._armed_timeout_s: float | None = None

    async def arm(self, timeout_s: float) -> None:
        plan = self.injector.consume(SimulatorFaultCode.WATCHDOG_FAULT)
        if plan is not None:
            self._activate_fault(
                code=plan.code.value,
                message=plan.message or "watchdog fault",
                **plan.details,
            )
            raise DeviceAdapterError(plan.message or "watchdog fault")
        self._armed_timeout_s = timeout_s
        self._heartbeat(state=DeviceOperationalState.READY, armed_timeout_s=timeout_s)

    async def kick(self) -> None:
        self._heartbeat(state=DeviceOperationalState.READY, armed_timeout_s=self._armed_timeout_s)

    async def disarm(self) -> None:
        self._armed_timeout_s = None
        self._heartbeat(state=DeviceOperationalState.DISABLED, armed_timeout_s=None)

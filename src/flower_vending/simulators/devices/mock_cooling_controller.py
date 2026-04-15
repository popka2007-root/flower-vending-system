"""Deterministic mock cooling controller."""

from __future__ import annotations

from flower_vending.devices.contracts import DeviceOperationalState
from flower_vending.devices.interfaces import CoolingController
from flower_vending.simulators.devices.base import MockManagedDevice


class MockCoolingController(MockManagedDevice, CoolingController):
    def __init__(self, name: str = "mock_cooling_controller") -> None:
        super().__init__(name)
        self.enabled = True
        self.target_celsius = 4.0

    async def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self._heartbeat(state=DeviceOperationalState.READY, enabled=enabled)

    async def set_target_celsius(self, target_celsius: float) -> None:
        self.target_celsius = target_celsius
        self._heartbeat(state=DeviceOperationalState.READY, target_celsius=target_celsius)

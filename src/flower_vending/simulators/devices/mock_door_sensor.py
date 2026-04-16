"""Deterministic mock service door sensor."""

from __future__ import annotations

from flower_vending.devices.contracts import DeviceCommandPolicy, DoorStatus
from flower_vending.devices.interfaces import DoorSensor
from flower_vending.simulators.devices.base import MockManagedDevice


class MockDoorSensor(MockManagedDevice, DoorSensor):
    def __init__(
        self,
        name: str = "mock_door_sensor",
        *,
        is_open: bool = False,
        command_policy: DeviceCommandPolicy | None = None,
    ) -> None:
        super().__init__(name, command_policy=command_policy)
        self._is_open = is_open

    def set_open(self, is_open: bool) -> None:
        self._is_open = is_open
        self._heartbeat(is_open=is_open)

    async def read_service_door(self) -> DoorStatus:
        self._heartbeat(is_open=self._is_open)
        return DoorStatus(sensor_name=self.name, is_open=self._is_open)

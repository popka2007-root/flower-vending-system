"""Deterministic mock temperature sensor."""

from __future__ import annotations

from flower_vending.devices.contracts import TemperatureReading
from flower_vending.devices.interfaces import TemperatureSensor
from flower_vending.simulators.devices.base import MockManagedDevice


class MockTemperatureSensor(MockManagedDevice, TemperatureSensor):
    def __init__(self, name: str = "mock_temperature_sensor", *, celsius: float = 4.0) -> None:
        super().__init__(name)
        self._celsius = celsius

    def set_celsius(self, celsius: float) -> None:
        self._celsius = celsius
        self._heartbeat(celsius=celsius)

    async def read_temperature(self) -> TemperatureReading:
        self._heartbeat(celsius=self._celsius)
        return TemperatureReading(sensor_name=self.name, celsius=self._celsius)

"""Machine-wide device health projection."""

from __future__ import annotations

from dataclasses import dataclass, field

from flower_vending.domain.value_objects import DeviceState


@dataclass(slots=True)
class DeviceHealthSnapshot:
    validator_state: DeviceState = DeviceState.UNKNOWN
    change_dispenser_state: DeviceState = DeviceState.UNKNOWN
    motor_state: DeviceState = DeviceState.UNKNOWN
    cooling_state: DeviceState = DeviceState.UNKNOWN
    window_state: DeviceState = DeviceState.UNKNOWN
    temperature_sensor_state: DeviceState = DeviceState.UNKNOWN
    door_sensor_state: DeviceState = DeviceState.UNKNOWN
    inventory_sensor_state: DeviceState = DeviceState.UNKNOWN
    watchdog_state: DeviceState = DeviceState.UNKNOWN
    last_heartbeat_at: str | None = None
    faults: list[str] = field(default_factory=list)

"""Health monitoring and machine sale blocking."""

from __future__ import annotations

from datetime import datetime, timezone

from flower_vending.app.event_bus import EventBus
from flower_vending.app.services.machine_status_service import MachineStatusService
from flower_vending.devices.contracts import DeviceOperationalState
from flower_vending.devices.interfaces import DoorSensor, ManagedDevice, TemperatureSensor
from flower_vending.domain.entities import DeviceHealthSnapshot
from flower_vending.domain.events.machine_events import machine_event
from flower_vending.domain.value_objects import DeviceState


class HealthMonitor:
    def __init__(
        self,
        *,
        devices: dict[str, ManagedDevice],
        machine_status_service: MachineStatusService,
        event_bus: EventBus,
        door_sensor: DoorSensor | None = None,
        temperature_sensor: TemperatureSensor | None = None,
        critical_temperature_celsius: float = 8.0,
    ) -> None:
        self._devices = devices
        self._machine_status_service = machine_status_service
        self._event_bus = event_bus
        self._door_sensor = door_sensor
        self._temperature_sensor = temperature_sensor
        self._critical_temperature_celsius = critical_temperature_celsius
        self._snapshot = DeviceHealthSnapshot()

    @property
    def snapshot(self) -> DeviceHealthSnapshot:
        return self._snapshot

    async def poll_once(self, correlation_id: str = "health-monitor") -> DeviceHealthSnapshot:
        faults: list[str] = []
        state_map: dict[str, DeviceState] = {}
        now_iso = datetime.now(tz=timezone.utc).isoformat()
        for name, device in self._devices.items():
            health = await device.get_health()
            state = DeviceState(health.state.value)
            state_map[name] = state
            if health.state in {
                DeviceOperationalState.FAULT,
                DeviceOperationalState.RECOVERY_PENDING,
                DeviceOperationalState.OUT_OF_SERVICE,
            }:
                faults.append(name)
        self._snapshot = DeviceHealthSnapshot(
            validator_state=state_map.get("validator", DeviceState.UNKNOWN),
            change_dispenser_state=state_map.get("change_dispenser", DeviceState.UNKNOWN),
            motor_state=state_map.get("motor", DeviceState.UNKNOWN),
            cooling_state=state_map.get("cooling", DeviceState.UNKNOWN),
            window_state=state_map.get("window", DeviceState.UNKNOWN),
            temperature_sensor_state=state_map.get("temperature", DeviceState.UNKNOWN),
            door_sensor_state=state_map.get("door", DeviceState.UNKNOWN),
            inventory_sensor_state=state_map.get("inventory", DeviceState.UNKNOWN),
            watchdog_state=state_map.get("watchdog", DeviceState.UNKNOWN),
            last_heartbeat_at=now_iso,
            faults=faults,
        )
        if faults:
            self._machine_status_service.block_sales("device_fault")
            await self._event_bus.publish(
                machine_event("machine_faulted", correlation_id=correlation_id, faults=faults)
            )
        else:
            self._machine_status_service.unblock_sales("device_fault")

        if self._door_sensor is not None:
            door = await self._door_sensor.read_service_door()
            if door.is_open:
                self._machine_status_service.block_sales("service_door_open")
                await self._event_bus.publish(
                    machine_event("service_door_opened", correlation_id=correlation_id)
                )
            else:
                self._machine_status_service.unblock_sales("service_door_open")

        if self._temperature_sensor is not None:
            reading = await self._temperature_sensor.read_temperature()
            if reading.celsius >= self._critical_temperature_celsius:
                self._machine_status_service.block_sales("critical_temperature")
                await self._event_bus.publish(
                    machine_event(
                        "critical_temperature_detected",
                        correlation_id=correlation_id,
                        celsius=reading.celsius,
                    )
                )
            else:
                self._machine_status_service.unblock_sales("critical_temperature")
        return self._snapshot

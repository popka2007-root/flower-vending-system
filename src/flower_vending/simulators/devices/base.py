"""Base classes for deterministic simulator devices."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from flower_vending.devices.contracts import DeviceFault, DeviceHealth, DeviceOperationalState, utc_now
from flower_vending.devices.interfaces import ManagedDevice
from flower_vending.simulators.faults import FaultInjectionPlan, FaultInjector, SimulatorFaultCode


class MockManagedDevice(ManagedDevice):
    """Common lifecycle and health behavior for simulator devices."""

    def __init__(self, name: str, *, injector: FaultInjector | None = None) -> None:
        self._name = name
        self._injector = injector or FaultInjector()
        self._started = False
        self._health = DeviceHealth(name=name, state=DeviceOperationalState.UNKNOWN)

    @property
    def name(self) -> str:
        return self._name

    @property
    def injector(self) -> FaultInjector:
        return self._injector

    async def start(self) -> None:
        self._started = True
        self._health = replace(
            self._health,
            state=DeviceOperationalState.READY,
            last_heartbeat_at=utc_now(),
            faults=(),
        )

    async def stop(self) -> None:
        self._started = False
        self._health = replace(
            self._health,
            state=DeviceOperationalState.DISABLED,
            last_heartbeat_at=utc_now(),
        )

    async def get_health(self) -> DeviceHealth:
        return self._health

    def inject_fault(
        self,
        code: SimulatorFaultCode,
        *,
        remaining_hits: int = 1,
        message: str | None = None,
        critical: bool = True,
        **details: Any,
    ) -> None:
        self._injector.add(
            FaultInjectionPlan(
                code=code,
                remaining_hits=remaining_hits,
                message=message,
                critical=critical,
                details=details,
            )
        )

    def clear_faults(self) -> None:
        self._injector.clear()
        self._health = replace(self._health, faults=(), state=DeviceOperationalState.READY)

    def _activate_fault(self, code: str, message: str, *, critical: bool = True, **details: Any) -> None:
        self._health = DeviceHealth(
            name=self.name,
            state=DeviceOperationalState.FAULT if critical else DeviceOperationalState.DEGRADED,
            last_heartbeat_at=utc_now(),
            faults=(DeviceFault(code=code, message=message, critical=critical, details=details),),
            details=details,
        )

    def _heartbeat(self, *, state: DeviceOperationalState | None = None, **details: Any) -> None:
        next_state = self._health.state if state is None else state
        self._health = DeviceHealth(
            name=self.name,
            state=next_state,
            last_heartbeat_at=utc_now(),
            faults=self._health.faults,
            details=details or self._health.details,
        )

"""Machine runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field

from flower_vending.domain.entities import DeviceHealthSnapshot, MachineStatus


@dataclass(slots=True)
class MachineRuntimeAggregate:
    status: MachineStatus = field(default_factory=MachineStatus)
    health_snapshot: DeviceHealthSnapshot = field(default_factory=DeviceHealthSnapshot)

    def block_sales(self, reason: str) -> None:
        self.status.block(reason)

    def unblock_sales(self, reason: str) -> None:
        self.status.unblock(reason)

"""Configuration models for the JCM DBV-300-SD adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from flower_vending.devices.contracts import DeviceCommandPolicy
from flower_vending.devices.exceptions import ConfigurationError


class DBV300TransportKind(StrEnum):
    SERIAL = "serial"
    MDB = "mdb"
    PULSE = "pulse"


class DBV300ProtocolKind(StrEnum):
    SERIAL = "serial"
    MDB = "mdb"
    PULSE = "pulse"


@dataclass(frozen=True, slots=True)
class SerialTransportSettings:
    port: str
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    read_timeout_s: float = 0.2
    write_timeout_s: float = 0.2

    def __post_init__(self) -> None:
        if not self.port:
            raise ConfigurationError("serial port must be provided")
        if self.baudrate <= 0:
            raise ConfigurationError("baudrate must be positive")
        if self.read_timeout_s <= 0 or self.write_timeout_s <= 0:
            raise ConfigurationError("serial timeouts must be positive")


@dataclass(frozen=True, slots=True)
class DBV300SDValidatorConfig:
    device_name: str = "jcm_dbv300sd"
    transport_kind: DBV300TransportKind = DBV300TransportKind.SERIAL
    protocol_kind: DBV300ProtocolKind = DBV300ProtocolKind.SERIAL
    serial_transport: SerialTransportSettings | None = None
    poll_interval_s: float = 0.2
    startup_disable_acceptance: bool = True
    fallback_disable_on_fault: bool = True
    accepted_denominations_minor: tuple[int, ...] = field(default_factory=tuple)
    command_policy: DeviceCommandPolicy = field(default_factory=DeviceCommandPolicy)

    def __post_init__(self) -> None:
        if not self.device_name:
            raise ConfigurationError("device_name must be provided")
        if self.poll_interval_s <= 0:
            raise ConfigurationError("poll_interval_s must be positive")
        if self.transport_kind is DBV300TransportKind.SERIAL and self.serial_transport is None:
            raise ConfigurationError(
                "serial_transport settings are required when transport_kind is 'serial'"
            )

    def require_serial_transport(self) -> SerialTransportSettings:
        if self.serial_transport is None:
            raise ConfigurationError("serial transport settings are not configured")
        return self.serial_transport

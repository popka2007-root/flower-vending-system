"""Shared device-layer DTOs and normalized device events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(tz=timezone.utc)


class DeviceOperationalState(StrEnum):
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    READY = "ready"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    FAULT = "fault"
    RECOVERY_PENDING = "recovery_pending"
    OUT_OF_SERVICE = "out_of_service"


class BillValidatorEventType(StrEnum):
    BILL_DETECTED = "bill_detected"
    BILL_VALIDATED = "bill_validated"
    BILL_REJECTED = "bill_rejected"
    ESCROW_AVAILABLE = "escrow_available"
    BILL_STACKED = "bill_stacked"
    BILL_RETURNED = "bill_returned"
    VALIDATOR_FAULT = "validator_fault"
    VALIDATOR_DISABLED = "validator_disabled"


class PayoutStatus(StrEnum):
    DISPENSED = "dispensed"
    PARTIAL = "partial"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"


class WindowPosition(StrEnum):
    UNKNOWN = "unknown"
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"


@dataclass(frozen=True, slots=True)
class MoneyValue:
    minor_units: int
    currency: str = "RUB"

    def __post_init__(self) -> None:
        if self.minor_units < 0:
            raise ValueError("minor_units must be non-negative")
        if not self.currency:
            raise ValueError("currency must be a non-empty string")


@dataclass(frozen=True, slots=True)
class DeviceFault:
    code: str
    message: str
    critical: bool = True
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeviceHealth:
    name: str
    state: DeviceOperationalState
    last_heartbeat_at: datetime | None = None
    faults: tuple[DeviceFault, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BillValidatorEvent:
    event_type: BillValidatorEventType
    validator_name: str
    occurred_at: datetime = field(default_factory=utc_now)
    correlation_id: str | None = None
    bill_value: MoneyValue | None = None
    sequence_number: int | None = None
    raw_payload: bytes | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProtocolCapabilities:
    escrow_supported: bool = False
    polling_required: bool = True
    push_events_supported: bool = False


@dataclass(frozen=True, slots=True)
class ValidatorProtocolEvent:
    event_type: BillValidatorEventType
    occurred_at: datetime = field(default_factory=utc_now)
    correlation_id: str | None = None
    bill_value: MoneyValue | None = None
    raw_payload: bytes | None = None
    sequence_number: int | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChangeDispenseRequest:
    request_id: str
    counts_by_denomination: Mapping[int, int]
    currency: str = "RUB"
    correlation_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChangeDispenseResult:
    request_id: str
    status: PayoutStatus
    paid_counts_by_denomination: Mapping[int, int] = field(default_factory=dict)
    details: Mapping[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class TemperatureReading:
    sensor_name: str
    celsius: float
    occurred_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class DoorStatus:
    sensor_name: str
    is_open: bool
    occurred_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class InventoryPresence:
    sensor_name: str
    slot_id: str
    has_product: bool
    confidence: float = 1.0
    occurred_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class PositionReading:
    sensor_name: str
    position_id: str
    in_position: bool
    is_home: bool = False
    occurred_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class WindowStatus:
    controller_name: str
    position: WindowPosition
    locked: bool = False
    occurred_at: datetime = field(default_factory=utc_now)

"""Normalized domain device state."""

from __future__ import annotations

from enum import StrEnum


class DeviceState(StrEnum):
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    READY = "ready"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    FAULT = "fault"
    RECOVERY_PENDING = "recovery_pending"
    OUT_OF_SERVICE = "out_of_service"

"""Device-layer exceptions."""

from __future__ import annotations


class DeviceAdapterError(RuntimeError):
    """Base exception for device adapter failures."""


class DeviceNotStartedError(DeviceAdapterError):
    """Raised when an operation requires a running adapter."""


class UnsupportedDeviceOperationError(DeviceAdapterError):
    """Raised when the configured device or protocol cannot perform an operation."""


class HardwareConfirmationRequiredError(DeviceAdapterError):
    """Raised when a real hardware or protocol detail must be confirmed first."""


class TransportIOError(DeviceAdapterError):
    """Raised on low-level transport read or write failures."""


class ProtocolDecodeError(DeviceAdapterError):
    """Raised when a wire-level message cannot be decoded safely."""


class ConfigurationError(DeviceAdapterError):
    """Raised when an adapter configuration is incomplete or inconsistent."""

"""SQLite-backed infrastructure persistence primitives."""

from flower_vending.infrastructure.persistence.sqlite.database import SQLiteDatabase
from flower_vending.infrastructure.persistence.sqlite.repositories import (
    AppliedConfigRepository,
    DeviceFaultLogRepository,
    DeviceSettingsRepository,
    MachineStatusRepository,
    MoneyInventoryRepository,
    OperationalEventRepository,
    ProductRepository,
    SlotRepository,
    TransactionRepository,
)
from flower_vending.infrastructure.persistence.sqlite.schema import (
    CURRENT_SCHEMA_VERSION,
    SCHEMA_SQL,
    ensure_sqlite_schema,
)

__all__ = [
    "AppliedConfigRepository",
    "CURRENT_SCHEMA_VERSION",
    "DeviceFaultLogRepository",
    "DeviceSettingsRepository",
    "MachineStatusRepository",
    "MoneyInventoryRepository",
    "OperationalEventRepository",
    "ProductRepository",
    "SCHEMA_SQL",
    "SQLiteDatabase",
    "SlotRepository",
    "TransactionRepository",
    "ensure_sqlite_schema",
]

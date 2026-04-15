"""Durable transaction journal for recovery-first persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from flower_vending.domain.events import DomainEvent
from flower_vending.infrastructure.persistence.sqlite.database import SQLiteDatabase


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class JournalEntryKind(StrEnum):
    INTENT = "intent"
    EVENT = "event"
    FAULT = "fault"
    RECOVERY = "recovery"


@dataclass(frozen=True, slots=True)
class JournalEntry:
    entry_kind: JournalEntryKind
    entry_name: str
    correlation_id: str
    transaction_id: str | None = None
    machine_state: str | None = None
    transaction_status: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = None
    created_at: datetime = field(default_factory=_utc_now)


class SQLiteTransactionJournal:
    """Append-only durable journal used as the recovery source of truth."""

    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def append_entry(self, entry: JournalEntry) -> int:
        return self._database.insert(
            """
            INSERT OR IGNORE INTO transaction_journal (
                transaction_id,
                correlation_id,
                entry_kind,
                entry_name,
                machine_state,
                transaction_status,
                payload_json,
                idempotency_key,
                created_at
            ) VALUES (
                :transaction_id,
                :correlation_id,
                :entry_kind,
                :entry_name,
                :machine_state,
                :transaction_status,
                :payload_json,
                :idempotency_key,
                :created_at
            )
            """,
            {
                "transaction_id": entry.transaction_id,
                "correlation_id": entry.correlation_id,
                "entry_kind": entry.entry_kind.value,
                "entry_name": entry.entry_name,
                "machine_state": entry.machine_state,
                "transaction_status": entry.transaction_status,
                "payload_json": self._database.dumps(entry.payload),
                "idempotency_key": entry.idempotency_key,
                "created_at": entry.created_at.isoformat(),
            },
        )

    def append_intent(
        self,
        *,
        intent_name: str,
        correlation_id: str,
        transaction_id: str | None = None,
        machine_state: str | None = None,
        transaction_status: str | None = None,
        idempotency_key: str | None = None,
        **payload: Any,
    ) -> int:
        return self.append_entry(
            JournalEntry(
                entry_kind=JournalEntryKind.INTENT,
                entry_name=intent_name,
                correlation_id=correlation_id,
                transaction_id=transaction_id,
                machine_state=machine_state,
                transaction_status=transaction_status,
                payload=dict(payload),
                idempotency_key=idempotency_key,
            )
        )

    def append_fault(
        self,
        *,
        fault_name: str,
        correlation_id: str,
        transaction_id: str | None = None,
        machine_state: str | None = None,
        transaction_status: str | None = None,
        idempotency_key: str | None = None,
        **payload: Any,
    ) -> int:
        return self.append_entry(
            JournalEntry(
                entry_kind=JournalEntryKind.FAULT,
                entry_name=fault_name,
                correlation_id=correlation_id,
                transaction_id=transaction_id,
                machine_state=machine_state,
                transaction_status=transaction_status,
                payload=dict(payload),
                idempotency_key=idempotency_key,
            )
        )

    def append_recovery_record(
        self,
        *,
        action_name: str,
        correlation_id: str,
        transaction_id: str | None = None,
        machine_state: str | None = None,
        transaction_status: str | None = None,
        idempotency_key: str | None = None,
        **payload: Any,
    ) -> int:
        return self.append_entry(
            JournalEntry(
                entry_kind=JournalEntryKind.RECOVERY,
                entry_name=action_name,
                correlation_id=correlation_id,
                transaction_id=transaction_id,
                machine_state=machine_state,
                transaction_status=transaction_status,
                payload=dict(payload),
                idempotency_key=idempotency_key,
            )
        )

    def append_event(
        self,
        event: DomainEvent,
        *,
        machine_state: str | None = None,
        transaction_status: str | None = None,
        idempotency_key: str | None = None,
    ) -> int:
        return self.append_entry(
            JournalEntry(
                entry_kind=JournalEntryKind.EVENT,
                entry_name=event.event_type,
                correlation_id=event.correlation_id,
                transaction_id=event.transaction_id,
                machine_state=machine_state,
                transaction_status=transaction_status,
                payload=dict(event.payload),
                idempotency_key=idempotency_key,
                created_at=event.occurred_at,
            )
        )

    async def handle_domain_event(
        self,
        event: DomainEvent,
        *,
        machine_state: str | None = None,
        transaction_status: str | None = None,
    ) -> None:
        self.append_event(
            event,
            machine_state=machine_state,
            transaction_status=transaction_status,
            idempotency_key=(
                f"event:{event.correlation_id}:{event.transaction_id or 'machine'}:"
                f"{event.event_type}:{event.occurred_at.isoformat()}"
            ),
        )

    def read_for_transaction(self, transaction_id: str) -> tuple[JournalEntry, ...]:
        rows = self._database.query_all(
            """
            SELECT
                transaction_id,
                correlation_id,
                entry_kind,
                entry_name,
                machine_state,
                transaction_status,
                payload_json,
                idempotency_key,
                created_at
            FROM transaction_journal
            WHERE transaction_id = ?
            ORDER BY journal_id ASC
            """,
            (transaction_id,),
        )
        return tuple(self._row_to_entry(row) for row in rows)

    def read_recent(self, limit: int = 100) -> tuple[JournalEntry, ...]:
        rows = self._database.query_all(
            """
            SELECT
                transaction_id,
                correlation_id,
                entry_kind,
                entry_name,
                machine_state,
                transaction_status,
                payload_json,
                idempotency_key,
                created_at
            FROM transaction_journal
            ORDER BY journal_id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return tuple(self._row_to_entry(row) for row in reversed(rows))

    def unresolved_transaction_ids(self) -> tuple[str, ...]:
        rows = self._database.query_all(
            """
            SELECT DISTINCT transaction_id
            FROM transaction_journal
            WHERE transaction_id IS NOT NULL
              AND (
                transaction_status IS NULL
                OR transaction_status NOT IN ('completed', 'cancelled')
              )
            ORDER BY transaction_id ASC
            """
        )
        return tuple(row["transaction_id"] for row in rows)

    def _row_to_entry(self, row: Any) -> JournalEntry:
        return JournalEntry(
            entry_kind=JournalEntryKind(row["entry_kind"]),
            entry_name=row["entry_name"],
            correlation_id=row["correlation_id"],
            transaction_id=row["transaction_id"],
            machine_state=row["machine_state"],
            transaction_status=row["transaction_status"],
            payload=self._database.loads(row["payload_json"], default={}) or {},
            idempotency_key=row["idempotency_key"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

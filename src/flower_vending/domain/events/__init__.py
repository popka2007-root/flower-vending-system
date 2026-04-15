"""Domain event contracts."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


def event_time() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_type: str
    correlation_id: str
    transaction_id: str | None = None
    occurred_at: datetime = field(default_factory=event_time)
    payload: Mapping[str, Any] = field(default_factory=dict)

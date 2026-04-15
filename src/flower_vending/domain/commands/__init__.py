"""Domain command contracts."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


def command_time() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass(frozen=True, slots=True)
class Command:
    correlation_id: str
    issued_at: datetime = field(default_factory=command_time, kw_only=True)

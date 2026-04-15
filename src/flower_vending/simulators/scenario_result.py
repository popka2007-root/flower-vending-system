"""Scenario result models for deterministic simulator runs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario_name: str
    success: bool
    machine_state: str
    transaction_id: str | None
    transaction_status: str | None
    event_types: tuple[str, ...] = ()
    sale_blockers: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(slots=True)
class EventRecorder:
    event_types: list[str] = field(default_factory=list)

    async def handle(self, event: object) -> None:
        event_type = getattr(event, "event_type", type(event).__name__)
        self.event_types.append(str(event_type))

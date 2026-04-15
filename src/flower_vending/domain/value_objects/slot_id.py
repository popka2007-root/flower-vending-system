"""Slot identity value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SlotId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("slot id must be non-empty")

"""Correlation identity value object."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class CorrelationId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("correlation id must be non-empty")

    @classmethod
    def new(cls) -> "CorrelationId":
        return cls(str(uuid4()))

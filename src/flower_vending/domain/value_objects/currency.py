"""Domain currency value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Currency:
    code: str = "RUB"

    def __post_init__(self) -> None:
        normalized = self.code.strip().upper()
        if not normalized:
            raise ValueError("currency code must be non-empty")
        object.__setattr__(self, "code", normalized)

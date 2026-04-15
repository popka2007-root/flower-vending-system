"""Transaction identity value object."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class TransactionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("transaction id must be non-empty")

    @classmethod
    def new(cls) -> "TransactionId":
        return cls(str(uuid4()))

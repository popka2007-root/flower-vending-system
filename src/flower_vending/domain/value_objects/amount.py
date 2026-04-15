"""Domain amount value object."""

from __future__ import annotations

from dataclasses import dataclass

from flower_vending.domain.value_objects.currency import Currency


@dataclass(frozen=True, slots=True)
class Amount:
    minor_units: int
    currency: Currency = Currency()

    def __post_init__(self) -> None:
        if self.minor_units < 0:
            raise ValueError("minor_units must be non-negative")

    def __add__(self, other: "Amount") -> "Amount":
        self._require_same_currency(other)
        return Amount(self.minor_units + other.minor_units, self.currency)

    def __sub__(self, other: "Amount") -> "Amount":
        self._require_same_currency(other)
        if other.minor_units > self.minor_units:
            raise ValueError("resulting amount would be negative")
        return Amount(self.minor_units - other.minor_units, self.currency)

    def __lt__(self, other: "Amount") -> bool:
        self._require_same_currency(other)
        return self.minor_units < other.minor_units

    def __le__(self, other: "Amount") -> bool:
        self._require_same_currency(other)
        return self.minor_units <= other.minor_units

    def __gt__(self, other: "Amount") -> bool:
        self._require_same_currency(other)
        return self.minor_units > other.minor_units

    def __ge__(self, other: "Amount") -> bool:
        self._require_same_currency(other)
        return self.minor_units >= other.minor_units

    @classmethod
    def zero(cls, currency: Currency | None = None) -> "Amount":
        return cls(minor_units=0, currency=currency or Currency())

    def is_zero(self) -> bool:
        return self.minor_units == 0

    def _require_same_currency(self, other: "Amount") -> None:
        if self.currency != other.currency:
            raise ValueError("currency mismatch")

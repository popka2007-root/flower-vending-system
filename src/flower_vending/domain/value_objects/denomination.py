"""Denomination domain value object."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from flower_vending.domain.value_objects.amount import Amount


class DenominationKind(StrEnum):
    BILL = "bill"
    COIN = "coin"


@dataclass(frozen=True, slots=True)
class Denomination:
    value: Amount
    kind: DenominationKind

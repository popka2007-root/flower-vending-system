"""Product entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from flower_vending.domain.value_objects import Amount, ProductId


@dataclass(slots=True)
class Product:
    product_id: ProductId
    name: str
    display_name: str
    price: Amount
    category: str
    is_bouquet: bool = False
    enabled: bool = True
    temperature_profile: str = "cooled"
    metadata: dict[str, Any] = field(default_factory=dict)

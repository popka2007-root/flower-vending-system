"""Screen-specific view models for the kiosk UI."""

from __future__ import annotations

from dataclasses import dataclass, field

from flower_vending.ui.viewmodels.common import ActionButtonViewModel, BannerViewModel


@dataclass(frozen=True, slots=True)
class CatalogCategoryViewModel:
    category_id: str
    label: str


@dataclass(frozen=True, slots=True)
class CatalogItemViewModel:
    product_id: str
    slot_id: str
    title: str
    category: str
    category_label: str
    price_text: str
    availability_text: str
    enabled: bool
    short_description: str | None = None
    image_path: str | None = None
    freshness_note: str | None = None
    size_label: str | None = None
    accent: str | None = None
    badge_text: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogScreenViewModel:
    title: str
    subtitle: str
    banner: BannerViewModel | None
    items: tuple[CatalogItemViewModel, ...]
    categories: tuple[CatalogCategoryViewModel, ...] = ()
    primary_action: ActionButtonViewModel | None = None
    secondary_action: ActionButtonViewModel | None = None


@dataclass(frozen=True, slots=True)
class ProductDetailsScreenViewModel:
    title: str
    subtitle: str
    price_text: str
    availability_text: str
    short_description: str | None
    image_path: str | None
    category_label: str | None
    freshness_note: str | None
    size_label: str | None
    badge_text: str | None
    advisory_text: str | None
    primary_action: ActionButtonViewModel
    secondary_action: ActionButtonViewModel


@dataclass(frozen=True, slots=True)
class PaymentScreenViewModel:
    title: str
    subtitle: str
    product_name: str
    price_text: str
    accepted_text: str
    remaining_text: str
    change_text: str
    help_text: str
    banner: BannerViewModel | None
    cancel_action: ActionButtonViewModel
    quick_insert_actions: tuple[ActionButtonViewModel, ...] = ()


@dataclass(frozen=True, slots=True)
class StatusScreenViewModel:
    title: str
    message: str
    details: tuple[str, ...] = ()
    banner: BannerViewModel | None = None
    primary_action: ActionButtonViewModel | None = None
    secondary_action: ActionButtonViewModel | None = None


@dataclass(frozen=True, slots=True)
class DeliveryScreenViewModel:
    title: str
    message: str
    details: tuple[str, ...] = ()
    banner: BannerViewModel | None = None
    primary_action: ActionButtonViewModel | None = None


@dataclass(frozen=True, slots=True)
class DiagnosticsDeviceViewModel:
    device_name: str
    state: str
    fault_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DiagnosticsScreenViewModel:
    title: str
    subtitle: str
    machine_state: str
    sale_blockers: tuple[str, ...]
    unresolved_transactions: tuple[str, ...]
    devices: tuple[DiagnosticsDeviceViewModel, ...] = ()
    recent_events: tuple[str, ...] = ()
    primary_action: ActionButtonViewModel | None = None


@dataclass(frozen=True, slots=True)
class ServiceScreenViewModel:
    title: str
    subtitle: str
    actions: tuple[ActionButtonViewModel, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

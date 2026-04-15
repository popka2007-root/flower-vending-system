"""Screen-specific view models for the kiosk UI."""

from __future__ import annotations

from dataclasses import dataclass, field

from flower_vending.ui.viewmodels.common import ActionButtonViewModel, BannerViewModel


@dataclass(frozen=True, slots=True)
class CatalogItemViewModel:
    product_id: str
    slot_id: str
    title: str
    category: str
    price_text: str
    availability_text: str
    enabled: bool
    badge_text: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogScreenViewModel:
    title: str
    subtitle: str
    banner: BannerViewModel | None
    items: tuple[CatalogItemViewModel, ...]
    primary_action: ActionButtonViewModel | None = None
    secondary_action: ActionButtonViewModel | None = None


@dataclass(frozen=True, slots=True)
class ProductDetailsScreenViewModel:
    title: str
    subtitle: str
    price_text: str
    availability_text: str
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

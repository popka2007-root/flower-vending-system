"""Catalog and product-card presentation logic."""

from __future__ import annotations

from flower_vending.ui.facade import CatalogEntry, MachineUiSnapshot
from flower_vending.ui.presenters.formatting import format_money
from flower_vending.ui.viewmodels.common import ActionButtonViewModel, BannerTone, BannerViewModel
from flower_vending.ui.viewmodels.screens import (
    CatalogItemViewModel,
    CatalogScreenViewModel,
    ProductDetailsScreenViewModel,
)


class CatalogPresenter:
    def present_catalog(
        self,
        *,
        title: str,
        subtitle: str,
        entries: tuple[CatalogEntry, ...],
        machine: MachineUiSnapshot,
    ) -> CatalogScreenViewModel:
        banner = None
        if machine.exact_change_only:
            banner = BannerViewModel(
                title="Только точная сумма",
                message="Наличная продажа доступна только без сдачи.",
                tone=BannerTone.WARNING,
            )
        items = tuple(self._item_view_model(entry) for entry in entries)
        return CatalogScreenViewModel(
            title=title,
            subtitle=subtitle,
            banner=banner,
            items=items,
            secondary_action=ActionButtonViewModel("open_service", "Сервис"),
        )

    def present_product_details(
        self,
        *,
        entry: CatalogEntry,
        machine: MachineUiSnapshot,
    ) -> ProductDetailsScreenViewModel:
        advisory = None
        if machine.exact_change_only:
            advisory = "Требуется точная сумма без сдачи."
        elif not entry.available:
            advisory = "Товар временно недоступен."
        return ProductDetailsScreenViewModel(
            title=entry.display_name,
            subtitle="Карточка товара",
            price_text=format_money(entry.price_minor_units, entry.currency_code),
            availability_text=f"Остаток: {entry.quantity}",
            advisory_text=advisory,
            primary_action=ActionButtonViewModel("start_cash_checkout", "Оплатить наличными", entry.available),
            secondary_action=ActionButtonViewModel("back_to_catalog", "Назад"),
        )

    def _item_view_model(self, entry: CatalogEntry) -> CatalogItemViewModel:
        badge = "Букет" if entry.is_bouquet else "Цветок"
        availability = "В наличии" if entry.available else "Нет в наличии"
        return CatalogItemViewModel(
            product_id=entry.product_id,
            slot_id=entry.slot_id,
            title=entry.display_name,
            category=entry.category,
            price_text=format_money(entry.price_minor_units, entry.currency_code),
            availability_text=availability,
            enabled=entry.available,
            badge_text=badge,
        )

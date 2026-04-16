"""Main Qt window for kiosk/touch UI."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, cast

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from flower_vending.ui.navigation import ScreenId
from flower_vending.ui.presenters import KioskPresenter, ScreenRender
from flower_vending.ui.theme import APP_STYLESHEET
from flower_vending.ui.views.screens import (
    CatalogScreenWidget,
    DeliveryScreenWidget,
    DiagnosticsScreenWidget,
    PaymentScreenWidget,
    ProductDetailsScreenWidget,
    ServiceScreenWidget,
    StatusScreenWidget,
)


def _install_cyrillic_font() -> None:
    app = cast(QApplication | None, QApplication.instance())
    if app is None:
        return
    candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    )
    for candidate in candidates:
        if not candidate.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(candidate))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            app.setFont(QFont(families[0]))
            return


class KioskMainWindow(QMainWindow):
    """Example kiosk window bound to the presenter/view-model layer."""

    def __init__(self, presenter: KioskPresenter, *, window_title: str = "Flower Vending Kiosk") -> None:
        super().__init__()
        _install_cyrillic_font()
        self._presenter = presenter
        self._presenter.subscribe(self.render_screen)
        self.setWindowTitle(window_title)
        self.resize(1280, 800)
        self.setMinimumSize(1024, 700)
        self.setStyleSheet(APP_STYLESHEET)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._catalog_screen = CatalogScreenWidget()
        self._product_screen = ProductDetailsScreenWidget()
        self._payment_screen = PaymentScreenWidget()
        self._status_screen = StatusScreenWidget()
        self._delivery_screen = DeliveryScreenWidget()
        self._service_screen = ServiceScreenWidget()
        self._diagnostics_screen = DiagnosticsScreenWidget()

        for widget in (
            self._catalog_screen,
            self._product_screen,
            self._payment_screen,
            self._status_screen,
            self._delivery_screen,
            self._service_screen,
            self._diagnostics_screen,
        ):
            self._stack.addWidget(widget)

        self._screen_map = {
            ScreenId.HOME: self._catalog_screen,
            ScreenId.CATALOG: self._catalog_screen,
            ScreenId.PRODUCT_DETAILS: self._product_screen,
            ScreenId.PAYMENT: self._payment_screen,
            ScreenId.EXACT_CHANGE: self._status_screen,
            ScreenId.NO_CHANGE: self._status_screen,
            ScreenId.ERROR: self._status_screen,
            ScreenId.SALES_BLOCKED: self._status_screen,
            ScreenId.RESTRICTED: self._status_screen,
            ScreenId.DISPENSING: self._delivery_screen,
            ScreenId.PICKUP: self._delivery_screen,
            ScreenId.SERVICE: self._service_screen,
            ScreenId.DIAGNOSTICS: self._diagnostics_screen,
        }

        self._catalog_screen.product_selected.connect(
            lambda product_id, slot_id: self._run_async(
                self._presenter.show_product_details(product_id, slot_id)
            )
        )
        self._catalog_screen.service_requested.connect(
            lambda: self._run_async(self._presenter.open_service_mode())
        )
        self._product_screen.back_requested.connect(lambda: self._run_async(self._presenter.back()))
        self._product_screen.pay_cash_requested.connect(
            lambda: self._run_async(self._presenter.start_cash_checkout())
        )
        self._payment_screen.cancel_requested.connect(
            lambda: self._run_async(self._presenter.cancel_purchase())
        )
        self._payment_screen.simulator_action_requested.connect(
            lambda action_id: self._run_async(self._presenter.handle_action(action_id))
        )
        self._status_screen.primary_action_requested.connect(self._handle_action)
        self._status_screen.secondary_action_requested.connect(self._handle_action)
        self._delivery_screen.primary_action_requested.connect(self._handle_action)
        self._service_screen.action_requested.connect(self._handle_action)
        self._diagnostics_screen.back_requested.connect(
            lambda: self._run_async(self._presenter.back())
        )
        self._diagnostics_screen.recover_requested.connect(
            lambda transaction_id: self._run_async(self._presenter.recover_transaction(transaction_id))
        )

    async def bootstrap(self) -> ScreenRender:
        return await self._presenter.initialize()

    def render_screen(self, render: ScreenRender) -> None:
        widget = self._screen_map[render.screen_id]
        bind = getattr(widget, "bind")
        bind(render.model)
        self._stack.setCurrentWidget(widget)

    def _handle_action(self, action_id: str) -> None:
        self._run_async(self._presenter.handle_action(action_id))

    def _run_async(self, coroutine: Coroutine[Any, Any, object]) -> None:
        asyncio.get_event_loop().create_task(coroutine)

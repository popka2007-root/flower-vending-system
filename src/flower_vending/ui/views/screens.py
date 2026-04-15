"""Qt widgets for kiosk screens."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from flower_vending.ui.viewmodels import (
    CatalogScreenViewModel,
    DeliveryScreenViewModel,
    DiagnosticsScreenViewModel,
    PaymentScreenViewModel,
    ProductDetailsScreenViewModel,
    ServiceScreenViewModel,
    StatusScreenViewModel,
)
from flower_vending.ui.widgets import BannerWidget, ProductTile, TouchButton


class CatalogScreenWidget(QWidget):
    product_selected = Signal(str, str)
    service_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("Subtitle")
        self._banner = BannerWidget()
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setSpacing(16)
        self._scroll.setWidget(self._grid_host)
        self._service_button = TouchButton("Сервис", secondary=True)
        self._service_button.clicked.connect(self.service_requested.emit)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._banner)
        layout.addWidget(self._scroll, 1)
        layout.addWidget(self._service_button)

    def bind(self, model: CatalogScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._banner.bind(model.banner)
        while self._grid.count():
            child = self._grid.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()
        for index, item in enumerate(model.items):
            tile = ProductTile()
            tile.bind(item)
            tile.selected.connect(self.product_selected.emit)
            row = index // 2
            column = index % 2
            self._grid.addWidget(tile, row, column)


class ProductDetailsScreenWidget(QWidget):
    pay_cash_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._card = QFrame()
        self._card.setObjectName("Card")
        card_layout = QVBoxLayout(self._card)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("Subtitle")
        self._price = QLabel()
        self._availability = QLabel()
        self._advisory = QLabel()
        self._advisory.setWordWrap(True)
        card_layout.addWidget(self._title)
        card_layout.addWidget(self._subtitle)
        card_layout.addSpacing(12)
        card_layout.addWidget(self._price)
        card_layout.addWidget(self._availability)
        card_layout.addWidget(self._advisory)
        buttons = QHBoxLayout()
        self._back = TouchButton("Назад", secondary=True)
        self._pay_cash = TouchButton("Оплатить наличными")
        self._back.clicked.connect(self.back_requested.emit)
        self._pay_cash.clicked.connect(self.pay_cash_requested.emit)
        buttons.addWidget(self._back)
        buttons.addWidget(self._pay_cash)
        layout.addWidget(self._card, 1)
        layout.addLayout(buttons)

    def bind(self, model: ProductDetailsScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._price.setText(f"Цена: {model.price_text}")
        self._availability.setText(model.availability_text)
        self._advisory.setText(model.advisory_text or "")
        self._advisory.setVisible(bool(model.advisory_text))
        self._pay_cash.setText(model.primary_action.label)
        self._pay_cash.setEnabled(model.primary_action.enabled)
        self._back.setText(model.secondary_action.label)


class PaymentScreenWidget(QWidget):
    cancel_requested = Signal()
    simulator_action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("Subtitle")
        self._banner = BannerWidget()
        self._product = QLabel()
        self._price = QLabel()
        self._accepted = QLabel()
        self._remaining = QLabel()
        self._change = QLabel()
        self._help = QLabel()
        self._help.setWordWrap(True)
        self._quick_insert_host = QWidget()
        self._quick_insert_layout = QHBoxLayout(self._quick_insert_host)
        self._cancel = TouchButton("Отменить", secondary=True)
        self._cancel.clicked.connect(self.cancel_requested.emit)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._banner)
        layout.addWidget(self._product)
        layout.addWidget(self._price)
        layout.addWidget(self._accepted)
        layout.addWidget(self._remaining)
        layout.addWidget(self._change)
        layout.addWidget(self._quick_insert_host)
        layout.addStretch(1)
        layout.addWidget(self._help)
        layout.addWidget(self._cancel)

    def bind(self, model: PaymentScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._banner.bind(model.banner)
        self._product.setText(f"Товар: {model.product_name}")
        self._price.setText(f"Стоимость: {model.price_text}")
        self._accepted.setText(f"Внесено: {model.accepted_text}")
        self._remaining.setText(f"Осталось: {model.remaining_text}")
        self._change.setText(f"Сдача: {model.change_text}")
        self._help.setText(model.help_text)
        self._cancel.setText(model.cancel_action.label)
        self._cancel.setEnabled(model.cancel_action.enabled)
        while self._quick_insert_layout.count():
            child = self._quick_insert_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()
        if not model.quick_insert_actions:
            self._quick_insert_host.hide()
        else:
            self._quick_insert_host.show()
            for action in model.quick_insert_actions:
                button = TouchButton(action.label)
                button.setEnabled(action.enabled)
                button.clicked.connect(
                    lambda checked=False, action_id=action.action_id: self.simulator_action_requested.emit(action_id)
                )
                self._quick_insert_layout.addWidget(button)


class StatusScreenWidget(QWidget):
    primary_action_requested = Signal(str)
    secondary_action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._message = QLabel()
        self._message.setWordWrap(True)
        self._banner = BannerWidget()
        self._details = QLabel()
        self._details.setWordWrap(True)
        self._primary = TouchButton("Далее")
        self._secondary = TouchButton("Назад", secondary=True)
        self._primary.clicked.connect(lambda: self.primary_action_requested.emit(self._primary.property("action_id")))
        self._secondary.clicked.connect(lambda: self.secondary_action_requested.emit(self._secondary.property("action_id")))
        layout.addWidget(self._title)
        layout.addWidget(self._banner)
        layout.addWidget(self._message)
        layout.addWidget(self._details)
        layout.addStretch(1)
        layout.addWidget(self._primary)
        layout.addWidget(self._secondary)

    def bind(self, model: StatusScreenViewModel) -> None:
        self._title.setText(model.title)
        self._message.setText(model.message)
        self._banner.bind(model.banner)
        self._details.setText("\n".join(model.details))
        self._details.setVisible(bool(model.details))
        if model.primary_action is None:
            self._primary.hide()
        else:
            self._primary.show()
            self._primary.setText(model.primary_action.label)
            self._primary.setEnabled(model.primary_action.enabled)
            self._primary.setProperty("action_id", model.primary_action.action_id)
        if model.secondary_action is None:
            self._secondary.hide()
        else:
            self._secondary.show()
            self._secondary.setText(model.secondary_action.label)
            self._secondary.setEnabled(model.secondary_action.enabled)
            self._secondary.setProperty("action_id", model.secondary_action.action_id)


class DeliveryScreenWidget(QWidget):
    primary_action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._message = QLabel()
        self._message.setWordWrap(True)
        self._banner = BannerWidget()
        self._details = QLabel()
        self._details.setWordWrap(True)
        self._primary = TouchButton("Подтвердить")
        self._primary.clicked.connect(lambda: self.primary_action_requested.emit(self._primary.property("action_id")))
        layout.addWidget(self._title)
        layout.addWidget(self._banner)
        layout.addWidget(self._message)
        layout.addWidget(self._details)
        layout.addStretch(1)
        layout.addWidget(self._primary)

    def bind(self, model: DeliveryScreenViewModel) -> None:
        self._title.setText(model.title)
        self._message.setText(model.message)
        self._banner.bind(model.banner)
        self._details.setText("\n".join(model.details))
        self._details.setVisible(bool(model.details))
        if model.primary_action is None:
            self._primary.hide()
        else:
            self._primary.show()
            self._primary.setText(model.primary_action.label)
            self._primary.setEnabled(model.primary_action.enabled)
            self._primary.setProperty("action_id", model.primary_action.action_id)


class ServiceScreenWidget(QWidget):
    action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("Subtitle")
        self._notes = QLabel()
        self._notes.setWordWrap(True)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._actions_host = QWidget()
        self._actions_layout = QVBoxLayout(self._actions_host)
        self._scroll.setWidget(self._actions_host)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._notes)
        layout.addWidget(self._scroll, 1)

    def bind(self, model: ServiceScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._notes.setText("\n".join(model.notes))
        while self._actions_layout.count():
            child = self._actions_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()
        for action in model.actions:
            button = TouchButton(action.label, secondary=action.action_id == "exit_service")
            button.setEnabled(action.enabled)
            button.clicked.connect(lambda checked=False, action_id=action.action_id: self.action_requested.emit(action_id))
            self._actions_layout.addWidget(button)


class DiagnosticsScreenWidget(QWidget):
    back_requested = Signal()
    recover_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("Subtitle")
        self._machine_state = QLabel()
        self._sale_blockers = QLabel()
        self._sale_blockers.setWordWrap(True)
        self._devices = QLabel()
        self._devices.setWordWrap(True)
        self._events = QLabel()
        self._events.setWordWrap(True)
        self._recovery_host = QWidget()
        self._recovery_layout = QVBoxLayout(self._recovery_host)
        self._back = TouchButton("Назад", secondary=True)
        self._back.clicked.connect(self.back_requested.emit)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._machine_state)
        layout.addWidget(self._sale_blockers)
        layout.addWidget(self._devices)
        layout.addWidget(self._events)
        layout.addWidget(self._recovery_host)
        layout.addStretch(1)
        layout.addWidget(self._back)

    def bind(self, model: DiagnosticsScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._machine_state.setText(f"FSM: {model.machine_state}")
        blockers = ", ".join(model.sale_blockers) if model.sale_blockers else "нет"
        self._sale_blockers.setText(f"Блокировки: {blockers}")
        device_lines = [f"{device.device_name}: {device.state}" for device in model.devices]
        self._devices.setText("Устройства:\n" + "\n".join(device_lines))
        self._events.setText("События:\n" + ("\n".join(model.recent_events) if model.recent_events else "нет"))
        while self._recovery_layout.count():
            child = self._recovery_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()
        for transaction_id in model.unresolved_transactions:
            button = TouchButton(f"Recover {transaction_id[:8]}")
            button.clicked.connect(
                lambda checked=False, tx_id=transaction_id: self.recover_requested.emit(tx_id)
            )
            self._recovery_layout.addWidget(button)

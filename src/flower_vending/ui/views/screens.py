"""Qt widgets for kiosk screens."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from flower_vending.ui.viewmodels import (
    CatalogCategoryViewModel,
    CatalogItemViewModel,
    CatalogScreenViewModel,
    DeliveryScreenViewModel,
    DiagnosticsScreenViewModel,
    PaymentScreenViewModel,
    ProductDetailsScreenViewModel,
    ServiceScreenViewModel,
    StatusScreenViewModel,
)
from flower_vending.ui.widgets import BannerWidget, ProductPhotoLabel, ProductTile, TouchButton


def _clear_layout(layout: QVBoxLayout | QHBoxLayout | QGridLayout) -> None:
    while layout.count():
        child = layout.takeAt(0)
        if child is None:
            continue
        widget = child.widget()
        if widget is not None:
            widget.deleteLater()


def _make_label(text: str = "", object_name: str | None = None) -> QLabel:
    label = QLabel(text)
    if object_name is not None:
        label.setObjectName(object_name)
    return label


class CatalogScreenWidget(QWidget):
    product_selected = Signal(str, str)
    service_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CustomerScreen")
        self._items: tuple[CatalogItemViewModel, ...] = ()
        self._categories: tuple[CatalogCategoryViewModel, ...] = ()
        self._tiles: list[ProductTile] = []
        self._active_category = "all"
        self._selected_product_id: str | None = None
        self._selected_slot_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 26, 32, 26)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(18)
        title_block = QVBoxLayout()
        title_block.setSpacing(4)
        self._title = _make_label(object_name="HeroTitle")
        self._subtitle = _make_label(object_name="HeroSubtitle")
        title_block.addWidget(self._title)
        title_block.addWidget(self._subtitle)

        self._service_panel = QFrame()
        self._service_panel.setObjectName("ServiceAccessPanel")
        service_layout = QVBoxLayout(self._service_panel)
        service_layout.setContentsMargins(8, 8, 8, 8)
        self._service_button = TouchButton("Сервис", secondary=True)
        self._service_button.setProperty("compact", True)
        self._service_button.clicked.connect(self.service_requested.emit)
        service_layout.addWidget(self._service_button)

        header.addLayout(title_block, 1)
        header.addWidget(self._service_panel, 0, Qt.AlignmentFlag.AlignTop)

        self._banner = BannerWidget()

        self._category_host = QWidget()
        self._category_host.setObjectName("CategoryBar")
        self._category_layout = QHBoxLayout(self._category_host)
        self._category_layout.setContentsMargins(0, 0, 0, 0)
        self._category_layout.setSpacing(8)
        self._category_group = QButtonGroup(self)
        self._category_group.setExclusive(True)

        body = QHBoxLayout()
        body.setSpacing(20)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(16)
        self._grid.setVerticalSpacing(16)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._scroll.setWidget(self._grid_host)

        self._purchase_panel = QFrame()
        self._purchase_panel.setObjectName("PurchasePanel")
        self._purchase_panel.setMinimumWidth(330)
        self._purchase_panel.setMaximumWidth(380)
        purchase_layout = QVBoxLayout(self._purchase_panel)
        purchase_layout.setContentsMargins(20, 20, 20, 20)
        purchase_layout.setSpacing(11)
        self._selected_caption = _make_label("Ваш выбор", "PanelCaption")
        self._selected_photo = ProductPhotoLabel(height=168)
        self._selected_title = _make_label("Выберите букет", "SelectedProductTitle")
        self._selected_title.setWordWrap(True)
        self._selected_description = _make_label("", "SelectedProductDescription")
        self._selected_description.setWordWrap(True)
        self._selected_meta = _make_label("", "ProductMeta")
        self._selected_meta.setWordWrap(True)
        self._selected_price = _make_label("", "SelectedPrice")
        self._selected_stock = _make_label("", "SelectedStock")
        self._primary_buy = TouchButton("Купить")
        self._primary_buy.clicked.connect(self._emit_selected_product)
        purchase_layout.addWidget(self._selected_caption)
        purchase_layout.addWidget(self._selected_photo)
        purchase_layout.addWidget(self._selected_title)
        purchase_layout.addWidget(self._selected_description)
        purchase_layout.addWidget(self._selected_meta)
        purchase_layout.addStretch(1)
        purchase_layout.addWidget(self._selected_price)
        purchase_layout.addWidget(self._selected_stock)
        purchase_layout.addWidget(self._primary_buy)

        body.addWidget(self._scroll, 1)
        body.addWidget(self._purchase_panel)

        layout.addLayout(header)
        layout.addWidget(self._banner)
        layout.addWidget(self._category_host)
        layout.addLayout(body, 1)

    def bind(self, model: CatalogScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._banner.bind(model.banner)
        self._items = model.items
        self._categories = model.categories
        if not any(category.category_id == self._active_category for category in self._categories):
            self._active_category = "all"
        self._render_categories()
        self._render_tiles()
        self._ensure_selection()
        self._refresh_selection()

    def _render_categories(self) -> None:
        _clear_layout(self._category_layout)
        self._category_group = QButtonGroup(self)
        self._category_group.setExclusive(True)
        for category in self._categories:
            button = TouchButton(category.label, secondary=True)
            button.setCheckable(True)
            button.setProperty("chip", True)
            button.setMinimumHeight(42)
            button.setChecked(category.category_id == self._active_category)
            button.clicked.connect(
                lambda checked=False, category_id=category.category_id: self._select_category(category_id)
            )
            self._category_group.addButton(button)
            self._category_layout.addWidget(button)
        self._category_layout.addStretch(1)

    def _render_tiles(self) -> None:
        _clear_layout(self._grid)
        self._tiles = []
        for index, item in enumerate(self._visible_items()):
            tile = ProductTile()
            tile.bind(item)
            tile.selected.connect(self._select_product)
            self._tiles.append(tile)
            row = index // 3
            column = index % 3
            self._grid.addWidget(tile, row, column)
        for column in range(3):
            self._grid.setColumnStretch(column, 1)

    def _visible_items(self) -> tuple[CatalogItemViewModel, ...]:
        if self._active_category == "all":
            return self._items
        return tuple(item for item in self._items if item.category == self._active_category)

    def _ensure_selection(self) -> None:
        current = self._selected_item()
        visible_items = self._visible_items()
        if current is not None and current.enabled and current in visible_items:
            return
        first_available = next((item for item in visible_items if item.enabled), None)
        self._selected_product_id = None if first_available is None else first_available.product_id
        self._selected_slot_id = None if first_available is None else first_available.slot_id

    def _select_category(self, category_id: str) -> None:
        self._active_category = category_id
        self._render_tiles()
        self._ensure_selection()
        self._refresh_selection()

    def _select_product(self, product_id: str, slot_id: str) -> None:
        self._selected_product_id = product_id
        self._selected_slot_id = slot_id
        self._refresh_selection()

    def _selected_item(self) -> CatalogItemViewModel | None:
        for item in self._items:
            if item.product_id == self._selected_product_id and item.slot_id == self._selected_slot_id:
                return item
        return None

    def _refresh_selection(self) -> None:
        selected = self._selected_item()
        for item, tile in zip(self._visible_items(), self._tiles, strict=False):
            tile.set_selected(item is selected)

        if selected is None:
            self._selected_photo.set_image(None, fallback_text="Выберите букет")
            self._selected_title.setText("Выберите букет")
            self._selected_description.clear()
            self._selected_meta.clear()
            self._selected_price.clear()
            self._selected_stock.clear()
            self._primary_buy.setEnabled(False)
            self._primary_buy.setText("Купить")
            return

        self._selected_photo.set_image(selected.image_path, fallback_text=selected.category_label)
        self._selected_title.setText(selected.title)
        self._selected_description.setText(selected.short_description or "")
        meta = " · ".join(
            text
            for text in (selected.category_label, selected.size_label, selected.freshness_note)
            if text
        )
        self._selected_meta.setText(meta)
        self._selected_price.setText(selected.price_text)
        self._selected_stock.setText(selected.availability_text)
        self._primary_buy.setText(f"Купить за {selected.price_text}")
        self._primary_buy.setEnabled(selected.enabled)

    def _emit_selected_product(self) -> None:
        selected = self._selected_item()
        if selected is None or not selected.enabled:
            return
        self.product_selected.emit(selected.product_id, selected.slot_id)


class ProductDetailsScreenWidget(QWidget):
    pay_cash_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CustomerScreen")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        self._card = QFrame()
        self._card.setObjectName("DetailsPanel")
        card_layout = QHBoxLayout(self._card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(26)
        self._photo = ProductPhotoLabel(height=410)
        self._photo.setMinimumWidth(420)
        self._photo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(12)
        self._subtitle = _make_label(object_name="HeroSubtitle")
        self._title = _make_label(object_name="HeroTitle")
        self._title.setWordWrap(True)
        self._description = _make_label(object_name="DetailDescription")
        self._description.setWordWrap(True)
        self._meta = _make_label(object_name="ProductMeta")
        self._meta.setWordWrap(True)
        self._price = _make_label(object_name="DetailPrice")
        self._availability = _make_label(object_name="SelectedStock")
        self._advisory = _make_label(object_name="HumanMessage")
        self._advisory.setWordWrap(True)
        info_layout.addWidget(self._subtitle)
        info_layout.addWidget(self._title)
        info_layout.addWidget(self._description)
        info_layout.addWidget(self._meta)
        info_layout.addSpacing(12)
        info_layout.addWidget(self._price)
        info_layout.addWidget(self._availability)
        info_layout.addWidget(self._advisory)
        info_layout.addStretch(1)

        card_layout.addWidget(self._photo, 1)
        card_layout.addLayout(info_layout, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(14)
        self._back = TouchButton("Назад", secondary=True)
        self._pay_cash = TouchButton("Оплатить")
        self._back.clicked.connect(self.back_requested.emit)
        self._pay_cash.clicked.connect(self.pay_cash_requested.emit)
        buttons.addWidget(self._back, 1)
        buttons.addWidget(self._pay_cash, 2)

        layout.addWidget(self._card, 1)
        layout.addLayout(buttons)

    def bind(self, model: ProductDetailsScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._description.setText(model.short_description or "")
        self._description.setVisible(bool(model.short_description))
        meta = " · ".join(
            text
            for text in (model.category_label, model.size_label, model.freshness_note, model.badge_text)
            if text
        )
        self._meta.setText(meta)
        self._price.setText(model.price_text)
        self._availability.setText(model.availability_text)
        self._advisory.setText(model.advisory_text or "")
        self._advisory.setVisible(bool(model.advisory_text))
        self._photo.set_image(model.image_path, fallback_text=model.category_label or "Букет")
        self._pay_cash.setText(model.primary_action.label)
        self._pay_cash.setEnabled(model.primary_action.enabled)
        self._back.setText(model.secondary_action.label)


class PaymentScreenWidget(QWidget):
    cancel_requested = Signal()
    simulator_action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CustomerScreen")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        self._title = _make_label(object_name="HeroTitle")
        self._subtitle = _make_label(object_name="HeroSubtitle")
        self._banner = BannerWidget()

        content = QHBoxLayout()
        content.setSpacing(20)

        customer_panel = QFrame()
        customer_panel.setObjectName("PaymentPanel")
        customer_layout = QVBoxLayout(customer_panel)
        customer_layout.setContentsMargins(24, 24, 24, 24)
        customer_layout.setSpacing(16)
        self._product = _make_label(object_name="PaymentProduct")
        metrics = QGridLayout()
        metrics.setHorizontalSpacing(14)
        metrics.setVerticalSpacing(14)
        self._price = self._add_metric(metrics, 0, 0, "К оплате")
        self._accepted = self._add_metric(metrics, 0, 1, "Внесено")
        self._remaining = self._add_metric(metrics, 1, 0, "Осталось")
        self._change = self._add_metric(metrics, 1, 1, "Сдача")
        self._help = _make_label(object_name="HumanMessage")
        self._help.setWordWrap(True)
        customer_layout.addWidget(self._product)
        customer_layout.addLayout(metrics)
        customer_layout.addStretch(1)
        customer_layout.addWidget(self._help)

        self._simulator_panel = QFrame()
        self._simulator_panel.setObjectName("SimulatorPanel")
        self._simulator_panel.setMinimumWidth(260)
        self._simulator_panel.setMaximumWidth(320)
        simulator_layout = QVBoxLayout(self._simulator_panel)
        simulator_layout.setContentsMargins(16, 16, 16, 16)
        simulator_layout.setSpacing(10)
        self._simulator_title = _make_label("Режим симулятора", "PanelCaption")
        self._simulator_hint = _make_label("Быстрое внесение купюр для теста", "SimulatorHint")
        self._simulator_hint.setWordWrap(True)
        self._quick_insert_host = QWidget()
        self._quick_insert_layout = QGridLayout(self._quick_insert_host)
        self._quick_insert_layout.setContentsMargins(0, 0, 0, 0)
        self._quick_insert_layout.setHorizontalSpacing(10)
        self._quick_insert_layout.setVerticalSpacing(10)
        simulator_layout.addWidget(self._simulator_title)
        simulator_layout.addWidget(self._simulator_hint)
        simulator_layout.addWidget(self._quick_insert_host)
        simulator_layout.addStretch(1)

        content.addWidget(customer_panel, 1)
        content.addWidget(self._simulator_panel)

        self._cancel = TouchButton("Отменить покупку", secondary=True)
        self._cancel.clicked.connect(self.cancel_requested.emit)

        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._banner)
        layout.addLayout(content, 1)
        layout.addWidget(self._cancel)

    def _add_metric(self, grid: QGridLayout, row: int, column: int, caption: str) -> QLabel:
        card = QFrame()
        card.setObjectName("MetricCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        metric_layout = QVBoxLayout(card)
        metric_layout.setContentsMargins(18, 16, 18, 16)
        metric_layout.setSpacing(4)
        label = _make_label(caption, "MetricCaption")
        value = _make_label(object_name="MetricValue")
        metric_layout.addWidget(label)
        metric_layout.addWidget(value)
        grid.addWidget(card, row, column)
        return value

    def bind(self, model: PaymentScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._banner.bind(model.banner)
        self._product.setText(model.product_name)
        self._price.setText(model.price_text)
        self._accepted.setText(model.accepted_text)
        self._remaining.setText(model.remaining_text)
        self._change.setText(model.change_text)
        self._help.setText(model.help_text)
        self._cancel.setText(model.cancel_action.label)
        self._cancel.setEnabled(model.cancel_action.enabled)
        _clear_layout(self._quick_insert_layout)
        if not model.quick_insert_actions:
            self._simulator_panel.hide()
            return
        self._simulator_panel.show()
        for index, action in enumerate(model.quick_insert_actions):
            button = TouchButton(action.label, secondary=True)
            button.setProperty("money", True)
            button.setEnabled(action.enabled)
            button.clicked.connect(
                lambda checked=False, action_id=action.action_id: self.simulator_action_requested.emit(action_id)
            )
            self._quick_insert_layout.addWidget(button, index // 2, index % 2)


class StatusScreenWidget(QWidget):
    primary_action_requested = Signal(str)
    secondary_action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CustomerScreen")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 34, 40, 34)
        layout.setSpacing(18)
        self._title = _make_label(object_name="HeroTitle")
        self._message = _make_label(object_name="StatusMessage")
        self._message.setWordWrap(True)
        self._banner = BannerWidget()
        self._details = _make_label(object_name="HumanMessage")
        self._details.setWordWrap(True)
        self._primary = TouchButton("Далее")
        self._secondary = TouchButton("Назад", secondary=True)
        self._primary.clicked.connect(lambda: self.primary_action_requested.emit(self._primary.property("action_id")))
        self._secondary.clicked.connect(
            lambda: self.secondary_action_requested.emit(self._secondary.property("action_id"))
        )
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
        self.setObjectName("CustomerScreen")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 34, 40, 34)
        layout.setSpacing(18)
        self._title = _make_label(object_name="HeroTitle")
        self._banner = BannerWidget()

        self._status_panel = QFrame()
        self._status_panel.setObjectName("DeliveryPanel")
        status_layout = QVBoxLayout(self._status_panel)
        status_layout.setContentsMargins(28, 28, 28, 28)
        status_layout.setSpacing(14)
        self._message = _make_label(object_name="DeliveryMessage")
        self._message.setWordWrap(True)
        self._details = _make_label(object_name="DeliveryDetails")
        self._details.setWordWrap(True)
        status_layout.addWidget(self._message)
        status_layout.addWidget(self._details)
        status_layout.addStretch(1)

        self._primary = TouchButton("Симулятор: букет забран", secondary=True)
        self._primary.setProperty("simulatorPrimary", True)
        self._primary.clicked.connect(lambda: self.primary_action_requested.emit(self._primary.property("action_id")))
        layout.addWidget(self._title)
        layout.addWidget(self._banner)
        layout.addWidget(self._status_panel, 1)
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
        self.setObjectName("ServiceScreen")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)
        self._title = _make_label(object_name="ServiceTitle")
        self._subtitle = _make_label(object_name="ServiceSubtitle")
        self._notes = _make_label(object_name="ServiceNotes")
        self._notes.setWordWrap(True)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._actions_host = QWidget()
        self._actions_layout = QVBoxLayout(self._actions_host)
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(10)
        self._scroll.setWidget(self._actions_host)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._notes)
        layout.addWidget(self._scroll, 1)

    def bind(self, model: ServiceScreenViewModel) -> None:
        self._title.setText(model.title)
        self._subtitle.setText(model.subtitle)
        self._notes.setText("\n".join(model.notes))
        _clear_layout(self._actions_layout)
        for action in model.actions:
            button = TouchButton(action.label, secondary=action.action_id == "exit_service")
            button.setProperty("serviceAction", True)
            button.setEnabled(action.enabled)
            button.clicked.connect(lambda checked=False, action_id=action.action_id: self.action_requested.emit(action_id))
            self._actions_layout.addWidget(button)


class DiagnosticsScreenWidget(QWidget):
    back_requested = Signal()
    recover_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ServiceScreen")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)
        self._title = _make_label(object_name="ServiceTitle")
        self._subtitle = _make_label(object_name="ServiceSubtitle")
        self._machine_state = _make_label(object_name="ServiceNotes")
        self._sale_blockers = _make_label(object_name="ServiceNotes")
        self._sale_blockers.setWordWrap(True)
        self._devices = _make_label(object_name="ServiceNotes")
        self._devices.setWordWrap(True)
        self._events = _make_label(object_name="ServiceNotes")
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
        _clear_layout(self._recovery_layout)
        for transaction_id in model.unresolved_transactions:
            button = TouchButton(f"Восстановить {transaction_id[:8]}")
            button.setProperty("serviceAction", True)
            button.clicked.connect(
                lambda checked=False, tx_id=transaction_id: self.recover_requested.emit(tx_id)
            )
            self._recovery_layout.addWidget(button)

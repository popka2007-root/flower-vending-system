"""Reusable touch-friendly Qt controls."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from flower_vending.ui.viewmodels import BannerViewModel, CatalogItemViewModel


class TouchButton(QPushButton):
    def __init__(self, label: str, *, secondary: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("secondary", secondary)


class BannerWidget(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._message = QLabel()
        self._message.setWordWrap(True)
        layout.addWidget(self._title)
        layout.addWidget(self._message)
        self.hide()

    def bind(self, banner: BannerViewModel | None) -> None:
        if banner is None:
            self.hide()
            return
        self._title.setText(banner.title)
        self._message.setText(banner.message)
        self._title.setProperty("tone", banner.tone.value)
        self._message.setProperty("tone", banner.tone.value)
        self.show()


class ProductTile(QFrame):
    selected = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setCursor(Qt.PointingHandCursor)
        self._product_id = ""
        self._slot_id = ""
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        self._title = QLabel()
        self._title.setObjectName("Title")
        self._badge = QLabel()
        self._badge.setProperty("badge", True)
        header.addWidget(self._title)
        header.addStretch(1)
        header.addWidget(self._badge)
        self._category = QLabel()
        self._category.setObjectName("Subtitle")
        self._price = QLabel()
        self._availability = QLabel()
        layout.addLayout(header)
        layout.addWidget(self._category)
        layout.addStretch(1)
        layout.addWidget(self._price)
        layout.addWidget(self._availability)

    def bind(self, item: CatalogItemViewModel) -> None:
        self._product_id = item.product_id
        self._slot_id = item.slot_id
        self._title.setText(item.title)
        self._badge.setText(item.badge_text or "")
        self._badge.setVisible(bool(item.badge_text))
        self._category.setText(item.category)
        self._price.setText(item.price_text)
        self._availability.setText(item.availability_text)
        self.setEnabled(item.enabled)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.selected.emit(self._product_id, self._slot_id)
        super().mouseReleaseEvent(event)

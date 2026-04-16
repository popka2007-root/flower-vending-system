"""Reusable touch-friendly Qt controls."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from flower_vending.ui.viewmodels import BannerViewModel, CatalogItemViewModel


def _repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class TouchButton(QPushButton):
    def __init__(self, label: str, *, secondary: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("secondary", secondary)
        self.setMinimumHeight(64)


class BannerWidget(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Banner")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)
        self._title = QLabel()
        self._title.setObjectName("BannerTitle")
        self._message = QLabel()
        self._message.setObjectName("BannerMessage")
        self._message.setWordWrap(True)
        layout.addWidget(self._title)
        layout.addWidget(self._message)
        self.hide()

    def bind(self, banner: BannerViewModel | None) -> None:
        if banner is None:
            self.hide()
            return
        tone = banner.tone.value
        self.setProperty("tone", tone)
        self._title.setText(banner.title)
        self._message.setText(banner.message)
        self._title.setProperty("tone", tone)
        self._message.setProperty("tone", tone)
        _repolish(self)
        _repolish(self._title)
        _repolish(self._message)
        self.show()


class ProductPhotoLabel(QLabel):
    def __init__(self, *, height: int = 150, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProductPhoto")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(height)
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setWordWrap(True)
        self._source_pixmap: QPixmap | None = None

    def set_image(self, image_path: str | None, *, fallback_text: str) -> None:
        pixmap = QPixmap(image_path) if image_path else QPixmap()
        self._source_pixmap = None if pixmap.isNull() else pixmap
        self.setProperty("hasImage", self._source_pixmap is not None)
        if self._source_pixmap is None:
            self.setPixmap(QPixmap())
            self.setText(fallback_text)
        else:
            self.setText("")
        _repolish(self)
        self._refresh_pixmap()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self) -> None:
        if self._source_pixmap is None or self.width() <= 0 or self.height() <= 0:
            return
        scaled = self._source_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - self.width()) // 2)
        y = max(0, (scaled.height() - self.height()) // 2)
        self.setPixmap(scaled.copy(x, y, min(self.width(), scaled.width()), min(self.height(), scaled.height())))


class ProductTile(QFrame):
    selected = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProductTile")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(270, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._product_id = ""
        self._slot_id = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)

        self._photo = ProductPhotoLabel(height=146)

        header = QHBoxLayout()
        header.setSpacing(8)
        self._title = QLabel()
        self._title.setObjectName("ProductTitle")
        self._title.setWordWrap(True)
        self._badge = QLabel()
        self._badge.setObjectName("Badge")
        header.addWidget(self._title, 1)
        header.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignTop)

        self._description = QLabel()
        self._description.setObjectName("ProductDescription")
        self._description.setWordWrap(True)
        self._description.setMinimumHeight(42)
        self._description.setMaximumHeight(50)
        self._category = QLabel()
        self._category.setObjectName("ProductMeta")
        self._category.setWordWrap(True)
        self._price = QLabel()
        self._price.setObjectName("ProductPrice")
        self._availability = QLabel()
        self._availability.setObjectName("StockLabel")

        layout.addWidget(self._photo)
        layout.addLayout(header)
        layout.addWidget(self._description)
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
        self._description.setText(item.short_description or "")
        self._description.setVisible(bool(item.short_description))
        meta = " · ".join(text for text in (item.category_label, item.freshness_note) if text)
        self._category.setText(meta)
        self._price.setText(item.price_text)
        self._availability.setText(item.availability_text)
        self._photo.set_image(item.image_path, fallback_text=item.category_label or "Букет")
        self.setProperty("available", item.enabled)
        self.setProperty("lowStock", item.availability_text == "Остался 1")
        self.setEnabled(item.enabled)
        _repolish(self)
        _repolish(self._availability)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        _repolish(self)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self.selected.emit(self._product_id, self._slot_id)
        super().mouseReleaseEvent(event)

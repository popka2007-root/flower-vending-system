"""Qt stylesheet and presentation constants for the kiosk UI."""

APP_STYLESHEET = """
QWidget {
    background: #fbfaf7;
    color: #201a1c;
    font-family: "Arial", "DejaVu Sans", "Noto Sans", "Segoe UI";
    font-size: 17px;
    letter-spacing: 0px;
}

QMainWindow,
QWidget#CustomerScreen {
    background: #fbfaf7;
}

QWidget#ServiceScreen {
    background: #eef3f8;
    color: #1e2937;
}

QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QLabel {
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 8px 0 8px 0;
}

QScrollBar::handle:vertical {
    background: #d3d9d1;
    border-radius: 6px;
    min-height: 64px;
}

QScrollBar::handle:vertical:hover {
    background: #b7c2b4;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
    border: none;
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 0 8px 0 8px;
}

QScrollBar::handle:horizontal {
    background: #d3d9d1;
    border-radius: 6px;
    min-width: 64px;
}

QScrollBar::handle:horizontal:hover {
    background: #b7c2b4;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
    border: none;
    width: 0px;
}

QLabel#HeroTitle {
    font-size: 36px;
    font-weight: 800;
    color: #24191f;
}

QLabel#HeroSubtitle {
    font-size: 20px;
    color: #5f6660;
}

QLabel#Title {
    font-size: 28px;
    font-weight: 700;
}

QLabel#Subtitle {
    font-size: 18px;
    color: #5f6660;
}

QFrame#Banner {
    background: #fff7df;
    border: 1px solid #e0b84d;
    border-radius: 8px;
}

QFrame#Banner[tone="success"] {
    background: #e9f7ef;
    border-color: #6fbd86;
}

QFrame#Banner[tone="error"] {
    background: #fff0f1;
    border-color: #d96b74;
}

QLabel#BannerTitle {
    font-size: 18px;
    font-weight: 800;
}

QLabel#BannerMessage {
    font-size: 16px;
    color: #51494c;
}

QFrame#ProductTile {
    background: #ffffff;
    border: 2px solid #e2ddd6;
    border-radius: 8px;
    min-height: 360px;
    padding: 0;
}

QFrame#ProductTile:hover {
    border-color: #b88a44;
    background: #fffdf8;
}

QFrame#ProductTile[selected="true"] {
    border: 2px solid #8f1f45;
    background: #fff8fb;
}

QFrame#ProductTile[available="false"] {
    background: #f1f0ed;
    border-color: #d5d2cc;
    color: #77736e;
}

QLabel#ProductPhoto {
    background: #f5f1ec;
    border: 1px solid #e1d8ce;
    border-radius: 8px;
    color: #7c6f68;
    font-size: 18px;
    font-weight: 800;
    padding: 0;
}

QLabel#ProductTitle {
    font-size: 20px;
    font-weight: 800;
    color: #24191f;
    line-height: 120%;
}

QLabel#ProductDescription,
QLabel#SelectedProductDescription,
QLabel#DetailDescription {
    font-size: 16px;
    color: #4d474b;
    font-weight: 500;
    line-height: 130%;
}

QLabel#ProductMeta {
    font-size: 15px;
    color: #5f6660;
    font-weight: 600;
    line-height: 120%;
}

QLabel#ProductPrice,
QLabel#SelectedPrice,
QLabel#DetailPrice {
    font-size: 30px;
    font-weight: 900;
    color: #8f1f45;
}

QLabel#StockLabel,
QLabel#SelectedStock {
    font-size: 16px;
    color: #1f6f4a;
    font-weight: 700;
}

QFrame#ProductTile[lowStock="true"] QLabel#StockLabel {
    color: #9a6617;
}

QLabel#Badge {
    background: #1f6f4a;
    color: white;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 13px;
    font-weight: 800;
}

QFrame#PurchasePanel,
QFrame#DetailsPanel,
QFrame#PaymentPanel,
QFrame#DeliveryPanel {
    background: #ffffff;
    border: 1px solid #e1dbd2;
    border-radius: 8px;
}

QFrame#ServiceAccessPanel {
    background: transparent;
    border: none;
    border-radius: 8px;
}

QLabel#ServiceAccessLabel,
QLabel#PanelCaption {
    color: #667085;
    font-size: 14px;
    font-weight: 800;
    text-transform: uppercase;
}

QLabel#SelectedProductTitle {
    font-size: 24px;
    font-weight: 850;
    color: #24191f;
}

QLabel#PaymentProduct {
    font-size: 28px;
    font-weight: 800;
    color: #24191f;
}

QFrame#MetricCard {
    background: #f7faf4;
    border: 1px solid #d8e7ce;
    border-radius: 8px;
    min-height: 128px;
}

QLabel#MetricCaption {
    color: #5f6660;
    font-size: 16px;
    font-weight: 800;
}

QLabel#MetricValue {
    color: #8f1f45;
    font-size: 34px;
    font-weight: 900;
}

QFrame#SimulatorPanel {
    background: #eef3f8;
    border: 1px solid #c7d2df;
    border-radius: 8px;
}

QLabel#SimulatorHint {
    color: #667085;
    font-size: 14px;
    font-weight: 600;
}

QLabel#HumanMessage {
    color: #474145;
    font-size: 18px;
    line-height: 130%;
}

QLabel#StatusMessage,
QLabel#DeliveryMessage {
    color: #24191f;
    font-size: 30px;
    font-weight: 800;
}

QLabel#DeliveryDetails {
    color: #474145;
    font-size: 22px;
    font-weight: 600;
}

QLabel#ServiceTitle {
    color: #1e2937;
    font-size: 32px;
    font-weight: 800;
}

QLabel#ServiceSubtitle,
QLabel#ServiceNotes {
    color: #475569;
    font-size: 17px;
}

QPushButton {
    min-height: 64px;
    padding: 10px 24px;
    border-radius: 8px;
    border: none;
    background: #8f1f45;
    color: #fffafc;
    font-size: 20px;
    font-weight: 800;
}

QPushButton:hover {
    background: #a82652;
}

QPushButton:pressed {
    background: #741737;
}

QPushButton:disabled {
    background: #c8c2bd;
    color: #f7f2ee;
}

QPushButton[secondary="true"] {
    background: #e8edf2;
    color: #223044;
    border: 1px solid #cbd5e1;
}

QPushButton[secondary="true"]:hover {
    background: #dbe4ec;
}

QPushButton[compact="true"] {
    min-height: 44px;
    padding: 6px 14px;
    font-size: 15px;
}

QPushButton[chip="true"] {
    min-height: 42px;
    padding: 6px 18px;
    font-size: 16px;
    font-weight: 800;
    background: #ffffff;
    color: #355847;
    border: 1px solid #cbd9c9;
}

QPushButton[chip="true"]:checked {
    background: #1f6f4a;
    color: #ffffff;
    border-color: #1f6f4a;
}

QPushButton[chip="true"]:hover {
    background: #eef7ef;
}

QPushButton[chip="true"]:checked:hover {
    background: #1f6f4a;
    color: #ffffff;
}

QPushButton[money="true"] {
    background: #ffffff;
    color: #1f6f4a;
    border: 2px solid #b9dcc6;
    min-height: 58px;
}

QPushButton[money="true"]:hover {
    background: #e9f7ef;
}

QPushButton[serviceAction="true"] {
    background: #ffffff;
    color: #1e2937;
    border: 1px solid #c7d2df;
    text-align: left;
}

QPushButton[serviceAction="true"]:hover {
    background: #e2eaf2;
}

QPushButton[simulatorPrimary="true"] {
    background: #eef3f8;
    color: #3b4858;
    border: 1px solid #c7d2df;
}
"""

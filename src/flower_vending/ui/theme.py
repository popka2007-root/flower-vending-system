"""Qt stylesheet and presentation constants for the kiosk UI."""

APP_STYLESHEET = """
QWidget {
    background: #f7f1e8;
    color: #2f2521;
    font-family: "Segoe UI";
    font-size: 16px;
}

QMainWindow {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #f6eee2,
        stop: 1 #ece1d0
    );
}

QFrame#Card {
    background: #fffaf4;
    border: 1px solid #d5c4ae;
    border-radius: 18px;
}

QLabel#Title {
    font-size: 28px;
    font-weight: 700;
}

QLabel#Subtitle {
    font-size: 18px;
    color: #6e5f54;
}

QPushButton {
    min-height: 64px;
    padding: 10px 24px;
    border-radius: 16px;
    border: none;
    background: #7f2335;
    color: #fff8f5;
    font-size: 18px;
    font-weight: 600;
}

QPushButton:hover {
    background: #972b41;
}

QPushButton:disabled {
    background: #b6a79b;
    color: #f2ece7;
}

QPushButton[secondary="true"] {
    background: #d8c8b7;
    color: #342a25;
}

QLabel[badge="true"] {
    background: #2f6b4f;
    color: white;
    border-radius: 10px;
    padding: 4px 10px;
    font-size: 13px;
    font-weight: 600;
}

QLabel[tone="warning"] {
    color: #9a5400;
}

QLabel[tone="error"] {
    color: #9d1f2b;
}

QLabel[tone="success"] {
    color: #1e6d4d;
}
"""

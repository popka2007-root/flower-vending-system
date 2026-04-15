"""Qt launcher for the simulator kiosk UI."""

from __future__ import annotations

import asyncio
import sys

from flower_vending.runtime.bootstrap import build_simulator_environment
from flower_vending.ui.presenters import KioskPresenter
from flower_vending.ui.views.kiosk_window import KioskMainWindow


def run_simulator_ui(*, config_path: str) -> int:
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:  # pragma: no cover - exercised only when PySide6 is missing
        raise RuntimeError(
            "PySide6 is not installed. Install the UI extra with: python -m pip install -e .[ui]"
        ) from exc

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    environment = loop.run_until_complete(
        build_simulator_environment(config_path=config_path, prepare_directories=True)
    )
    loop.run_until_complete(environment.start())

    app = QApplication(sys.argv)
    presenter = KioskPresenter(environment.ui_facade)
    window = KioskMainWindow(presenter, window_title=environment.config.ui.window_title)
    loop.run_until_complete(window.bootstrap())

    if environment.config.ui.kiosk_fullscreen:
        window.showFullScreen()
    else:
        window.show()

    timer = QTimer()

    def pump_asyncio() -> None:
        if loop.is_closed():
            timer.stop()
            return
        loop.call_soon(loop.stop)
        loop.run_forever()

    def shutdown() -> None:
        timer.stop()
        if loop.is_closed():
            return
        loop.run_until_complete(environment.stop())
        loop.close()

    timer.timeout.connect(pump_asyncio)
    timer.start(10)
    app.aboutToQuit.connect(shutdown)
    return app.exec()

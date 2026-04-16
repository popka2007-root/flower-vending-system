"""Create the simulator kiosk window offscreen and capture a smoke screenshot."""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CONFIG = ROOT / "config" / "examples" / "machine.simulator.yaml"
SCREENSHOT = ROOT / "artifacts" / "ui-smoke-catalog.png"
STATE_ROOT = ROOT / "artifacts" / "ui-smoke-state"


def _prepare_import_path() -> None:
    for path in (ROOT, SRC):
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)


def _reset_smoke_state() -> None:
    artifacts = (ROOT / "artifacts").resolve()
    state_root = STATE_ROOT.resolve()
    if artifacts not in (state_root, *state_root.parents):
        raise AssertionError(f"refusing to remove state outside artifacts: {state_root}")
    if state_root.exists():
        shutil.rmtree(state_root)
    state_root.mkdir(parents=True, exist_ok=True)
    os.environ["FLOWER_VENDING_STATE_ROOT"] = str(state_root)


def _assert_nonblank_screenshot(image: object) -> None:
    qimage = image.toImage()
    colors: set[int] = set()
    x_step = max(1, qimage.width() // 24)
    y_step = max(1, qimage.height() // 18)
    for y in range(0, qimage.height(), y_step):
        for x in range(0, qimage.width(), x_step):
            colors.add(qimage.pixel(x, y))
    if len(colors) < 12:
        raise AssertionError("catalog screenshot looks blank or nearly monochrome")


async def _run_smoke() -> None:
    from PySide6.QtWidgets import QApplication, QLabel

    from flower_vending.runtime.bootstrap import build_simulator_environment
    from flower_vending.ui.presenters import KioskPresenter
    from flower_vending.ui.views.kiosk_window import KioskMainWindow

    _reset_smoke_state()
    app = QApplication.instance() or QApplication(["ui-smoke"])
    environment = await build_simulator_environment(
        config_path=str(CONFIG),
        prepare_directories=True,
    )
    await environment.start()
    try:
        presenter = KioskPresenter(environment.ui_facade)
        window = KioskMainWindow(presenter, window_title="UI smoke")
        await window.bootstrap()
        window.resize(1280, 800)
        window.show()
        app.processEvents()
        if window.centralWidget() is None:
            raise AssertionError("kiosk window has no central widget")
        product_photos = window.findChildren(QLabel, "ProductPhoto")
        loaded_photos = [
            label
            for label in product_photos
            if label.pixmap() is not None and not label.pixmap().isNull()
        ]
        if not loaded_photos:
            raise AssertionError("no product images were loaded on the catalog screen")
        screenshot = window.grab()
        if screenshot.isNull():
            raise AssertionError("failed to grab kiosk screenshot")
        _assert_nonblank_screenshot(screenshot)
        SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
        if not screenshot.save(str(SCREENSHOT)):
            raise AssertionError(f"failed to save screenshot: {SCREENSHOT}")
        window.close()
        app.processEvents()
        app.closeAllWindows()
    finally:
        await environment.stop()
        app.processEvents()
        QApplication.sendPostedEvents(None, 0)
        QApplication.processEvents()
        QApplication.restoreOverrideCursor()
        app.setQuitOnLastWindowClosed(True)
        app.quit()


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "0")
    _prepare_import_path()
    try:
        import PySide6  # noqa: F401
    except ImportError:
        print("SKIP: PySide6 is not installed; UI smoke check was not run.")
        return 0
    asyncio.run(_run_smoke())
    print(f"PASS: UI smoke screenshot saved to {SCREENSHOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

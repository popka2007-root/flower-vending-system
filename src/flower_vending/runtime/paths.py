"""Runtime path helpers for source and bundled deployments."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR_NAME = "FlowerVendingSystem"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def bundle_root() -> Path:
    configured = os.getenv("FLOWER_VENDING_RESOURCE_ROOT")
    if configured:
        return Path(configured).resolve()
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return discover_source_root()


def state_root() -> Path:
    configured = os.getenv("FLOWER_VENDING_STATE_ROOT")
    if configured:
        return Path(configured).resolve()
    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data).resolve() / APP_DIR_NAME
        return Path.home().resolve() / "AppData" / "Local" / APP_DIR_NAME
    xdg_state_home = os.getenv("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home).resolve() / "flower-vending-system"
    return Path.home().resolve() / ".local" / "state" / "flower-vending-system"


def discover_source_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__).resolve()).resolve()
    for path in (current, *current.parents):
        if (path / "pyproject.toml").exists():
            return path
    raise FileNotFoundError("unable to locate project root containing pyproject.toml")

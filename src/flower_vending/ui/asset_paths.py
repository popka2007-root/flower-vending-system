"""Resolve packaged UI assets for source and PyInstaller runs."""

from __future__ import annotations

import sys
from pathlib import Path


def resolve_ui_asset_path(raw_path: str | None) -> str | None:
    if raw_path is None:
        return None
    normalized = raw_path.strip().replace("\\", "/")
    if not normalized:
        return None

    direct = Path(normalized)
    if direct.is_absolute():
        return str(direct) if direct.exists() else None

    ui_dir = Path(__file__).resolve().parent
    bundle_root = Path(getattr(sys, "_MEIPASS", ui_dir.parents[2]))
    candidates = (
        ui_dir / "assets" / normalized,
        ui_dir / normalized,
        bundle_root / normalized,
        bundle_root / "src" / normalized,
        bundle_root / "flower_vending" / "ui" / "assets" / normalized,
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None

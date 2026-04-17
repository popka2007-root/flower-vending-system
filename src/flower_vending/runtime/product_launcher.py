"""Packaged application launcher for end-user desktop builds."""

from __future__ import annotations

import os
import shutil

from flower_vending.runtime.paths import bundle_root, state_root
from flower_vending.runtime.ui_runner import run_simulator_ui


def run_packaged_simulator_app() -> int:
    resource_root = bundle_root()
    writable_root = state_root()
    docs_target = writable_root / "docs"
    docs_target.mkdir(parents=True, exist_ok=True)

    bundled_docs = resource_root / "docs"
    if bundled_docs.exists():
        for source in bundled_docs.rglob("*"):
            if not source.is_file():
                continue
            target = docs_target / source.relative_to(bundled_docs)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

    os.environ.setdefault("FLOWER_VENDING_RESOURCE_ROOT", str(resource_root))
    os.environ.setdefault("FLOWER_VENDING_STATE_ROOT", str(writable_root))
    config_path = resource_root / "config" / "examples" / "machine.simulator.yaml"
    return run_simulator_ui(config_path=str(config_path))


if __name__ == "__main__":
    raise SystemExit(run_packaged_simulator_app())

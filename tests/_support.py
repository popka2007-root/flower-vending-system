"""Shared helpers for stdlib test execution."""

from __future__ import annotations

import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from flower_vending.simulators.harness import SimulationHarness  # noqa: E402


class AsyncHarnessTestCase(unittest.IsolatedAsyncioTestCase):
    async def create_harness(self, **kwargs: object) -> SimulationHarness:
        harness = SimulationHarness.build(**kwargs)
        await harness.start()
        self.addAsyncCleanup(harness.stop)
        return harness


@contextmanager
def workspace_temp_dir(prefix: str = "tmp") -> Iterator[Path]:
    root = ROOT / "var" / "tmp"
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=prefix, dir=root) as tmp:
        yield Path(tmp)

"""Repository-root module entrypoint shim."""

from __future__ import annotations

from flower_vending.runtime.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

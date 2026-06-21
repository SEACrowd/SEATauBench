"""Allow ``python -m seatau.plot`` to use the shared dispatcher."""

from __future__ import annotations

from seatau.plot.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

"""sunset-engine scorecard | playbook APP-ID [--inventory PATH]"""
from __future__ import annotations

import argparse
from pathlib import Path

from .inventory import load_inventory
from .playbook import playbook
from .report import scorecard
from .spi import rank

DEFAULT = Path(__file__).resolve().parents[2] / "data" / "app_inventory.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sunset-engine")
    ap.add_argument("--inventory", default=str(DEFAULT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scorecard")
    pb = sub.add_parser("playbook")
    pb.add_argument("app_id", nargs="?", help="defaults to the highest-priority Retire candidate")
    args = ap.parse_args(argv)

    results = rank(load_inventory(args.inventory))
    if args.cmd == "scorecard":
        print(scorecard(results))
        return 0
    target = next((r for r in results if r.app.app_id == args.app_id), None) if args.app_id else \
        next((r for r in results if r.disposition == "Retire"), None)
    if target is None:
        print("No matching application.")
        return 1
    print(f"# Decommissioning playbook — {target.app.name} ({target.app.app_id})\n")
    print("\n".join(playbook(target)))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

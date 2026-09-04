#!/usr/bin/env python3
"""Alfred Script Filter entry point."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.bridge import BridgeError, search as bridge_search
from lib.results import alfred_json, item_payload, parse_search_output, status_item


def _placeholder() -> str:
    return alfred_json(
        [
            {
                "title": "Search iCloud Passwords",
                "subtitle": "Type a site, app, URL, user name, or email",
                "valid": False,
                "arg": "",
            }
        ]
    )


def _items_from_search(query: str) -> str:
    try:
        raw = bridge_search(query)
    except BridgeError as err:
        return alfred_json([status_item(err.status)])
    except Exception:
        return alfred_json([status_item("ERROR")])
    status, rows = parse_search_output(raw)
    if status != "OK":
        item = status_item(status)
        if status == "LOCKED":
            item["valid"] = False
            item["subtitle"] = "Unlock Passwords if it appeared. Come back to Alfred and type the search again."
        rerun = 0.8 if status in {"LOCKED", "NEED_AX"} else None
        return alfred_json([item], rerun=rerun)
    items = [item_payload(entry) for entry in rows[:40]]
    if not items:
        return alfred_json([status_item("EMPTY", "Try another site, URL, or email")])
    return alfred_json(items)


def main(argv: list[str]) -> int:
    query = argv[1] if len(argv) > 1 else ""
    query = query.strip()
    if not query:
        sys.stdout.write(_placeholder())
        return 0
    sys.stdout.write(_items_from_search(query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

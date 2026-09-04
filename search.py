#!/usr/bin/env python3
"""Alfred Script Filter. Live results as you type."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.bridge import BridgeError, search as bridge_search
from lib.cache import local_hits, save
from lib.results import alfred_json, item_payload, parse_search_output, status_item


def _placeholder() -> str:
    return alfred_json(
        [
            {
                "title": "Type a site, URL, or email",
                "subtitle": "Example: pw arizona",
                "valid": False,
                "arg": "",
            }
        ]
    )


def _items(rows: list[dict[str, str]]) -> str:
    items = [item_payload(entry) for entry in rows[:20]]
    if not items:
        return alfred_json([status_item("EMPTY", "Try another site, URL, or email")])
    return alfred_json(items)


def _items_from_passwords(query: str) -> str:
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
            item["valid"] = True
            item["arg"] = __import__("json").dumps({"cmd": "unlock"})
            item["subtitle"] = "Return opens Passwords for Touch ID. Results appear here after unlock."
        if status == "NEED_AX":
            item["valid"] = True
            item["arg"] = __import__("json").dumps({"cmd": "ax"})
            item["subtitle"] = "Return opens Accessibility. Enable Alfred and searchax, then type again."
        rerun = 0.5 if status in {"LOCKED", "NEED_AX"} else None
        return alfred_json([item], rerun=rerun)
    save(query, rows)
    return _items(rows)


def main(argv: list[str]) -> int:
    query = argv[1] if len(argv) > 1 else ""
    query = query.strip()
    if not query:
        sys.stdout.write(_placeholder())
        return 0
    cached = local_hits(query)
    if cached is not None:
        sys.stdout.write(_items(cached))
        return 0
    sys.stdout.write(_items_from_passwords(query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

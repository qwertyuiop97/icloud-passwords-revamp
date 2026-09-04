#!/usr/bin/env python3
"""Alfred Script Filter. Live results as you type. Never fronts Passwords."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.bridge import BridgeError, front_context, probe_vault, search as bridge_search
from lib.cache import invalidate, local_hits, save
from lib.context import query_from_front
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


def _items(rows: list[dict[str, str]], *, cached: bool = False, context: bool = False) -> str:
    items = [item_payload(entry) for entry in rows[:20]]
    if not items:
        return alfred_json([status_item("EMPTY", "Try another site, URL, or email")])
    if context:
        for item in items:
            item["subtitle"] = (item.get("subtitle") or "") + "  ·  current site"
            vars_ = item.setdefault("variables", {})
            vars_["source"] = "context"
    if cached:
        for item in items:
            item["subtitle"] = (item.get("subtitle") or "") + "  ·  cached"
            vars_ = item.setdefault("variables", {})
            vars_["source"] = "cache"
    return alfred_json(items)


def _status_json(status: str) -> str:
    item = status_item(status)
    if status == "LOCKED":
        item["valid"] = True
        item["arg"] = json.dumps({"cmd": "unlock"})
        item["subtitle"] = (
            "Return opens Passwords for Touch ID. Typing leaves it in the background."
        )
    if status == "NOT_RUNNING":
        item["valid"] = True
        item["arg"] = json.dumps({"cmd": "unlock"})
        item["subtitle"] = "Return opens Passwords. Typing will not launch it."
    if status == "NO_APP":
        item["valid"] = False
        item["subtitle"] = "Install Passwords from macOS, then Return."
    if status == "NEED_AX":
        item["valid"] = True
        item["arg"] = json.dumps({"cmd": "ax"})
        item["subtitle"] = "Return opens Accessibility. Enable Alfred and searchax, then type again."
    rerun = 0.8 if status in {"LOCKED", "NEED_AX", "NOT_RUNNING"} else None
    return alfred_json([item], rerun=rerun)


def _items_from_passwords(query: str, *, context: bool = False) -> str:
    try:
        raw = bridge_search(query)
    except BridgeError as err:
        invalidate()
        return _status_json(err.status)
    except Exception:
        invalidate()
        return _status_json("ERROR")
    status, rows = parse_search_output(raw)
    if status != "OK":
        invalidate()
        return _status_json(status)
    save(query, rows)
    tagged = [{**row, "source": "context"} for row in rows] if context else rows
    return _items(tagged, context=context)


def _context_query() -> str:
    try:
        app_name, url, title = front_context()
    except Exception:
        return ""
    return query_from_front(app_name, url, title)


def main(argv: list[str]) -> int:
    query = argv[1] if len(argv) > 1 else ""
    query = query.strip()
    state = probe_vault()
    if state != "UNLOCKED":
        invalidate()
        sys.stdout.write(_status_json(state))
        return 0
    if not query:
        ctx = _context_query()
        if ctx:
            cached = local_hits(ctx)
            if cached is not None:
                sys.stdout.write(_items(cached, cached=True, context=True))
                return 0
            sys.stdout.write(_items_from_passwords(ctx, context=True))
            return 0
        sys.stdout.write(_placeholder())
        return 0
    cached = local_hits(query)
    if cached is not None:
        sys.stdout.write(_items(cached, cached=True))
        return 0
    sys.stdout.write(_items_from_passwords(query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

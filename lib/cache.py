"""On-disk metadata cache so typing can filter without hitting Passwords."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .results import matches, parse_search_output


def _path() -> Path:
    root = os.environ.get("alfred_workflow_cache") or "/tmp/icloud-passwords-revamp"
    Path(root).mkdir(parents=True, exist_ok=True)
    return Path(root) / "meta.json"


def load() -> dict:
    path = _path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def save(query: str, rows: list[dict[str, str]]) -> None:
    payload = {"q": query, "rows": rows, "ts": time.time()}
    _path().write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")


def local_hits(query: str) -> list[dict[str, str]] | None:
    """Return cached rows if this query only narrows a previous search."""
    data = load()
    prev = str(data.get("q") or "")
    rows = data.get("rows")
    if not prev or not isinstance(rows, list):
        return None
    q = query.lower()
    p = prev.lower()
    if not q.startswith(p) and not p.startswith(q):
        return None
    if q.startswith(p):
        return [row for row in rows if isinstance(row, dict) and matches(row, query)]
    return None


def rows_from_output(raw: str) -> tuple[str, list[dict[str, str]]]:
    return parse_search_output(raw)

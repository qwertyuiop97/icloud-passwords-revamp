"""Alfred Script Filter JSON. Rows are site + username only."""

from __future__ import annotations

import json
import re
from typing import Any, Iterable

MASKED = re.compile(r"^[•●∙·*.\s]+$")
SIDEBAR_TITLES = {
    "all",
    "all passwords",
    "passkeys",
    "codes",
    "wi-fi",
    "wifi",
    "security",
    "deleted",
    "generated passwords",
    "verification codes",
}
STATUS_TITLES = {
    "NO_APP": "Install the Passwords app (macOS Sequoia or later)",
    "NOT_RUNNING": "Passwords isn't running",
    "NEED_AX": "Enable Accessibility for Alfred, then search again",
    "LOCKED": "Unlock Passwords with Touch ID",
    "EMPTY": "No matching logins",
    "ERROR": "Could not search Passwords",
}
STATUS_SUB = {
    "LOCKED": "Return opens Passwords for Touch ID. Typing leaves it in the background.",
    "NOT_RUNNING": "Return opens Passwords. Typing will not launch it.",
    "NO_APP": "Install Passwords from macOS, then Return.",
    "NEED_AX": "System Settings → Privacy & Security → Accessibility → Alfred",
}


def is_masked_secret(text: str) -> bool:
    return bool(text) and bool(MASKED.fullmatch(text))


def parse_search_output(raw: str) -> tuple[str, list[dict[str, str]]]:
    """Parse TSV from the UI bridge. First line is a status token."""
    lines = [line.rstrip("\n") for line in raw.splitlines() if line.strip()]
    if not lines:
        return "ERROR", []
    status = lines[0].strip()
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if "\t" not in line:
            continue
        title, username = line.split("\t", 1)
        title, username = title.strip(), username.strip()
        if not title:
            continue
        if is_masked_secret(title) or is_masked_secret(username):
            continue
        if title.lower() in SIDEBAR_TITLES:
            continue
        rows.append({"title": title, "username": username})
    return status, rows


def tokenize(query: str) -> list[str]:
    return [part.lower() for part in re.split(r"\s+", query.strip()) if part]


def haystack(entry: dict[str, str]) -> str:
    """Searchable metadata: site name, username/email, URL-like strings."""
    title = entry.get("title") or ""
    username = entry.get("username") or ""
    url = entry.get("url") or ""
    bits = [title, username, url]
    for value in (title, url):
        bits.extend(re.split(r"[/:._\-@]+", value))
    if "@" in username:
        local, _, domain = username.partition("@")
        bits.extend([local, domain])
    return " ".join(bits).lower()


def matches(entry: dict[str, str], query: str) -> bool:
    tokens = tokenize(query)
    if not tokens:
        return False
    text = haystack(entry)
    return all(token in text for token in tokens)


def item_payload(entry: dict[str, str], action: str = "fill") -> dict[str, Any]:
    site = entry.get("title") or ""
    username = entry.get("username") or ""

    display_title = username if username else site
    display_sub = site if username else "Login"
    if entry.get("source") in {"tab", "context"} and site:
        display_sub = f"{site}  ·  current site"
    arg = json.dumps({"title": site, "username": username}, separators=(",", ":"))
    return {
        "title": display_title,
        "subtitle": display_sub,
        "arg": arg,
        "autocomplete": username or site,
        "valid": True,
        "text": {"copy": username, "largetype": f"{site}\n{username}"},
        "variables": {"action": action},
        "mods": {
            "cmd": {
                "subtitle": "Copy password (concealed clipboard)",
                "variables": {"action": "copy_password"},
            },
            "alt": {
                "subtitle": "Copy verification code",
                "variables": {"action": "copy_otp"},
            },
            "ctrl": {
                "subtitle": "Copy user name",
                "variables": {"action": "copy_username"},
            },
            "shift": {
                "subtitle": "Open in Passwords",
                "variables": {"action": "reveal"},
            },
        },
    }


def status_item(status: str, detail: str = "") -> dict[str, Any]:
    title = STATUS_TITLES.get(status, STATUS_TITLES["ERROR"])
    item: dict[str, Any] = {
        "title": title,
        "subtitle": detail or STATUS_SUB.get(status, ""),
        "valid": False,
        "arg": "",
    }
    if status in {"LOCKED", "NEED_AX", "NOT_RUNNING"}:
        item["rerun"] = 0.8
    return item


def filter_items(query: str, entries: Iterable[dict[str, str]]) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        return [
            {
                "title": "Search iCloud Passwords",
                "subtitle": "Type a site, app, URL, user name, or email",
                "valid": False,
                "arg": "",
            }
        ]
    matched = [entry for entry in entries if matches(entry, query)]
    return [item_payload(entry) for entry in matched[:40]]


def alfred_json(items: list[dict[str, Any]], *, rerun: float | None = None) -> str:
    payload: dict[str, Any] = {"skipknowledge": True, "items": items}
    if rerun:
        payload["rerun"] = rerun
    if items and items[0].get("rerun") and not rerun:
        payload["rerun"] = items[0]["rerun"]
        items[0].pop("rerun", None)
    return json.dumps(payload, ensure_ascii=False)

"""Read the frontmost browser tab URL. Never reads page content or passwords."""

from __future__ import annotations

import re
from urllib.parse import urlparse

BROWSER_HOST_RE = re.compile(
    r"^(www\.)?(?P<host>[a-z0-9.-]+\.[a-z]{2,})(?::\d+)?",
    re.I,
)


def host_from_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def search_query_from_url(url: str) -> str:
    """Use the registrable host so `arizona.edu` matches WebAuth."""
    host = host_from_url(url)
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host

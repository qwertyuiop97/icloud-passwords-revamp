"""Frontmost app / URL → search query. Only the front process is contacted."""

from __future__ import annotations

from .tab import search_query_from_url

BROWSERS = {
    "safari",
    "safari technology preview",
    "google chrome",
    "chromium",
    "microsoft edge",
    "brave browser",
    "arc",
    "zen",
    "firefox",
    "orion",
    "vivaldi",
    "dia",
}

SKIP_APPS = {
    "alfred",
    "alfred 5",
    "alfred 4",
    "alfred preferences",
    "passwords",
    "finder",
    "loginwindow",
    "system events",
}


def query_from_front(app_name: str, url: str = "", window_title: str = "") -> str:
    """Return a short search query, or empty if there is nothing useful."""
    url_q = search_query_from_url(url or "")
    if url_q:
        return url_q
    app = (app_name or "").strip()
    if not app or app.lower() in SKIP_APPS:
        return ""
    if app.lower() in BROWSERS:
        title = (window_title or "").strip()
        return search_query_from_url(title) if title else ""
    return app

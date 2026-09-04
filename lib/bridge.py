"""Run ui.applescript. stdout is status/metadata, never a password."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_SCRIPT = ROOT / "ui.applescript"
TIMEOUT = 25


class BridgeError(RuntimeError):
    def __init__(self, status: str, detail: str = ""):
        super().__init__(status)
        self.status = status
        self.detail = detail


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("HISTFILE", None)
    return env


def _run(args: list[str], timeout: int = TIMEOUT) -> str:
    completed = subprocess.run(
        ["/usr/bin/osascript", str(UI_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_env(),
        check=False,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if completed.returncode != 0:
        combined = (stdout + "\n" + stderr).strip()
        if "not allowed assistive access" in combined or "-25211" in combined:
            raise BridgeError("NEED_AX", "Accessibility")
        raise BridgeError("ERROR", "osascript failed")
    return stdout


def _first_token(raw: str) -> str:
    for line in raw.splitlines():
        token = line.strip()
        if token:
            return token
    return ""


def _search_cmd(cmd: list[str], timeout: float) -> str:
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_env(),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "LOCKED\n"
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if completed.returncode != 0:
        combined = (stdout + "\n" + stderr).strip()
        if "not allowed assistive access" in combined or "-25211" in combined:
            return "NEED_AX\n"
        if _first_token(stdout) in {
            "OK",
            "EMPTY",
            "LOCKED",
            "NEED_AX",
            "NO_APP",
            "NOT_RUNNING",
            "UNLOCKED",
        }:
            return stdout
        return ""
    return stdout


def _searchax() -> Path:
    return ROOT / "searchax"


def _jxa() -> Path:
    return ROOT / "search_ui.js"


def probe_vault() -> str:
    """Background lock check. Never opens or focuses Passwords."""
    binary = _searchax()
    if binary.is_file() and os.access(binary, os.X_OK):
        token = _first_token(_search_cmd([str(binary), "--state"], 1.5))
        if token in {"UNLOCKED", "LOCKED", "NEED_AX", "NO_APP", "NOT_RUNNING"}:
            return token
    js = _jxa()
    token = _first_token(
        _search_cmd(["/usr/bin/osascript", "-l", "JavaScript", str(js), "--state"], 2)
    )
    if token in {"UNLOCKED", "LOCKED", "NEED_AX", "NO_APP", "NOT_RUNNING"}:
        return token
    return "LOCKED"


_CHROME_URL = (
    "Google Chrome",
    "Chromium",
    "Microsoft Edge",
    "Brave Browser",
    "Arc",
    "Vivaldi",
    "Dia",
)
_SAFARI_URL = ("Safari", "Safari Technology Preview")


def _url_of_front_browser(app_name: str) -> str:
    """Ask only the already-frontmost browser. Never probes other browsers."""
    if app_name in _CHROME_URL:
        src = f'tell application "{app_name}" to get URL of active tab of front window'
    elif app_name in _SAFARI_URL:
        src = f'tell application "{app_name}" to get URL of current tab of front window'
    else:
        return ""
    try:
        completed = subprocess.run(
            ["/usr/bin/osascript", "-e", src],
            capture_output=True,
            text=True,
            timeout=2,
            env=_env(),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ""
    if completed.returncode != 0:
        return ""
    return (completed.stdout or "").strip()


def front_context() -> tuple[str, str, str]:
    """Frontmost non-Alfred app, URL, window title. Never launches a browser."""
    raw = _run(["frontcontext"], timeout=4)
    parts = (raw or "").split("\t")
    while len(parts) < 3:
        parts.append("")
    app_name, _empty, title = parts[0].strip(), parts[1].strip(), parts[2].strip()
    url = _url_of_front_browser(app_name) if app_name else ""
    return app_name, url, title


def search(query: str) -> str:
    binary = _searchax()
    js = _jxa()
    if binary.is_file() and os.access(binary, os.X_OK):
        raw = _search_cmd([str(binary), query], 2.0)
        token = _first_token(raw)
        if token:
            return raw
    js_raw = _search_cmd(
        ["/usr/bin/osascript", "-l", "JavaScript", str(js), query],
        4,
    )
    if _first_token(js_raw):
        return js_raw
    return "LOCKED\n"


def inspect_fields(app_name: str) -> str:
    return _run(["inspect", app_name])


def copy_menu(kind: str, title: str, username: str) -> str:
    """Tell Passwords to copy a field. The secret stays in the pasteboard."""
    if kind not in {"username", "password", "otp"}:
        raise BridgeError("ERROR", "bad copy kind")
    return _run(["copy", kind, title, username])


def reveal(title: str, username: str) -> str:
    return _run(["reveal", title, username])


def frontmost_app() -> str:
    return _run(["frontmost"]).strip()


def activate_app(name: str) -> None:
    _run(["activate", name])


def paste_into(kind: str) -> str:
    if kind not in {"username", "password"}:
        raise BridgeError("ERROR", "bad paste kind")
    return _run(["paste", kind])


def stamp_concealed() -> None:
    _run(["conceal"])


def clear_clipboard() -> None:
    _run(["clearclip"])


def quit_passwords() -> None:
    try:
        _run(["quit"], timeout=8)
    except BridgeError:
        return

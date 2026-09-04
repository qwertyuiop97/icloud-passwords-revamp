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
        if _first_token(stdout) in {"OK", "EMPTY", "LOCKED", "NEED_AX", "NO_APP"}:
            return stdout
        return ""
    return stdout


def search(query: str) -> str:
    binary = ROOT / "searchax"
    js = ROOT / "search_ui.js"
    last = ""
    if binary.is_file() and os.access(binary, os.X_OK):
        last = _search_cmd([str(binary), query], 2.2)
        if _first_token(last) == "OK":
            return last
    js_raw = _search_cmd(
        ["/usr/bin/osascript", "-l", "JavaScript", str(js), query],
        5,
    )
    token = _first_token(js_raw)
    if token == "OK" or token == "EMPTY":
        return js_raw
    if token:
        last = js_raw
    try:
        as_raw = _run(["search", query], timeout=8)
    except subprocess.TimeoutExpired:
        as_raw = ""
    except BridgeError as err:
        if last:
            return last
        raise err
    if _first_token(as_raw) == "OK" or _first_token(as_raw):
        return as_raw
    return last or "ERROR\n"


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

"""Talk to ui.applescript. Never log or return password values."""

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


def _run(args: list[str], timeout: int = TIMEOUT) -> str:
    env = os.environ.copy()
    # Keep secrets out of crash logs we control.
    env.pop("HISTFILE", None)
    completed = subprocess.run(
        ["/usr/bin/osascript", str(UI_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
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


def search(query: str) -> str:
    return _run(["search", query])


def tab_url() -> str:
    try:
        return _run(["taburl"], timeout=8).strip()
    except BridgeError:
        return ""


def inspect_fields(app_name: str) -> str:
    return _run(["inspect", app_name])


def copy_menu(kind: str, title: str, username: str) -> str:
    """Ask Passwords to copy a field via its own menu. We do not read it."""
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

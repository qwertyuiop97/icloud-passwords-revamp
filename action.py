#!/usr/bin/env python3
"""Fill or copy the login selected in Alfred."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.bridge import (
    BridgeError,
    activate_app,
    clear_clipboard,
    copy_menu,
    frontmost_app,
    inspect_fields,
    paste_into,
    quit_passwords,
    reveal,
    stamp_concealed,
)
from lib.fill import parse_account, steps_for
from lib.inspect import parse_fields


def _notify(title: str, message: str) -> None:
    # title/message are labels, not secrets.
    subprocess.run(
        [
            "/usr/bin/osascript",
            "-e",
            "on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run",
            title,
            message,
        ],
        check=False,
        capture_output=True,
    )


def _target_app() -> str:
    for _ in range(8):
        name = frontmost_app()
        if name and name not in {"Alfred", "Alfred 5", "Alfred 4", "Alfred Preferences", "Passwords"}:
            return name
        time.sleep(0.12)
    return frontmost_app()


def main(argv: list[str]) -> int:
    action = os.environ.get("action") or "fill"
    arg = argv[1] if len(argv) > 1 else ""
    if not arg:
        _notify("iCloud Passwords", "No login selected.")
        return 1
    try:
        peeked = json.loads(arg)
        if isinstance(peeked, dict) and peeked.get("cmd") == "unlock":
            subprocess.run(["/usr/bin/open", "-a", "Passwords"], check=False)
            return 0
    except Exception:
        pass
    try:
        account = parse_account(arg)
    except ValueError:
        _notify("iCloud Passwords", "Could not read the selected login.")
        return 1

    title = account["title"]
    username = account["username"]

    if action == "reveal":
        reveal(title, username)
        return 0

    target = _target_app()
    fields: list[dict] = []
    if action == "fill":
        try:
            activate_app(target)
            time.sleep(0.15)
            raw_fields = inspect_fields(target)
            fields = parse_fields(raw_fields)
        except BridgeError:
            fields = []

    fill_both = (os.environ.get("fill_both") or "1") == "1"
    try:
        steps = steps_for(action, fields, fill_both=fill_both)
    except ValueError:
        _notify("iCloud Passwords", "Refusing to paste a password into a user name field.")
        return 1

    last_copy = ""
    for step in steps:
        menu = step.get("menu")
        if menu in {"username", "password", "otp"}:
            result = copy_menu(menu, title, username)
            if result.strip() != "OK":
                _notify("iCloud Passwords", f"Could not copy {menu.replace('_', ' ')}.")
                return 1
            last_copy = menu
            if step.get("conceal") == "yes":
                stamp_concealed()
        paste = step.get("paste")
        if paste in {"username", "password"}:
            activate_app(target)
            time.sleep(0.12)
            try:
                paste_into(paste)
            except BridgeError:
                _notify(
                    "iCloud Passwords",
                    "Stopped: would have pasted a password into the wrong field.",
                )
                clear_clipboard()
                return 1
        if step.get("clear") == "yes":
            time.sleep(0.2)
            clear_clipboard()

    if action == "fill":
        _notify("iCloud Passwords", f"Filled {title}")
    elif last_copy == "password":
        _notify("iCloud Passwords", "Password copied")
    elif last_copy == "otp":
        _notify("iCloud Passwords", "Verification code copied")
    elif last_copy == "username":
        _notify("iCloud Passwords", "User name copied")
    if (os.environ.get("close_after_copy") or "1") == "1" and action != "reveal":
        quit_passwords()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

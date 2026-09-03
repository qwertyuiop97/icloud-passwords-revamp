#!/usr/bin/env python3
"""Resolve Passwords.app menu titles for the current macOS language."""

from __future__ import annotations

import plistlib
import subprocess
import sys
from pathlib import Path

STRINGS_ROOT = Path(
    "/System/Library/PrivateFrameworks/PasswordManagerUI.framework/"
    "Versions/A/Resources"
)

KEYS = {
    "copy_password": "Copy Password (from context menu/menu bar item)",
    "copy_username": "Copy User Name (from context menu/menu bar item)",
    "copy_otp": "Copy Verification Code (Menu Item)",
    "search": "Search (menu item)",
    "unlock": "Unlock",
    "all_passwords": "All Passwords",
}

DEFAULTS = {
    "copy_password": "Copy Password",
    "copy_username": "Copy User Name",
    "copy_otp": "Copy Code",
    "search": "Search",
    "unlock": "Unlock",
    "all_passwords": "All Passwords",
}

ORDER = (
    "copy_password",
    "copy_username",
    "copy_otp",
    "search",
    "unlock",
    "all_passwords",
)


def preferred_langs() -> list[str]:
    try:
        raw = subprocess.check_output(
            ["/usr/bin/defaults", "read", "-g", "AppleLanguages"],
            text=True,
        )
    except subprocess.CalledProcessError:
        return ["en"]

    langs: list[str] = []
    for line in raw.splitlines():
        token = line.strip().strip(",").strip('"').strip("'")
        if not token or token in "()":
            continue
        langs.append(token)
    return langs or ["en"]


def lproj_names(lang: str) -> list[str]:
    compact = lang.replace("-", "_")
    names = [compact]
    if "_" in compact:
        names.append(compact.split("_", 1)[0])
    if "en" not in names:
        names.append("en")
    return names


def load_strings(lproj: str) -> dict[str, str]:
    path = STRINGS_ROOT / f"{lproj}.lproj" / "Localizable.strings"
    if not path.is_file():
        return {}
    try:
        data = plistlib.loads(path.read_bytes())
    except Exception:
        return {}
    return {str(k): str(v) for k, v in data.items()}


def resolve() -> dict[str, str]:
    titles = dict(DEFAULTS)
    for lang in preferred_langs():
        for candidate in lproj_names(lang):
            strings = load_strings(candidate)
            if not strings:
                continue
            for field, key in KEYS.items():
                if key in strings and strings[key]:
                    titles[field] = strings[key]
            if candidate != "en" or lang.startswith("en"):
                return titles
    return titles


def main() -> int:
    titles = resolve()
    sys.stdout.write("\t".join(titles[key] for key in ORDER))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

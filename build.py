#!/usr/bin/env python3
"""Generate info.plist and the installable .alfredworkflow archive."""

from __future__ import annotations

import plistlib
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUNDLE_ID = "com.qwertyuiop97.alfred-icloud-passwords"
REPO_URL = "https://github.com/qwertyuiop97/alfred-icloud-passwords"

OBJECTS = {
    "kw_search": "keyword.search",
    "kw_password": "keyword.password",
    "kw_otp": "keyword.otp",
    "arg_find": "arg.find",
    "arg_password": "arg.password",
    "arg_otp": "arg.otp",
    "arg_username": "arg.username",
    "script": "action.script",
}

MOD_CMD = 1048576
MOD_OPT = 524288
MOD_CTRL = 262144


def uid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"alfred://{BUNDLE_ID}/{name}")).upper()


def keyword(uid_name: str, var: str, text: str, subtext: str) -> dict:
    return {
        "config": {
            "argumenttype": 0,
            "keyword": f"{{var:{var}}}",
            "subtext": subtext,
            "text": text,
            "withspace": True,
        },
        "type": "alfred.workflow.input.keyword",
        "uid": uid(uid_name),
        "version": 1,
    }


def arg_and_vars(uid_name: str, mode: str) -> dict:
    return {
        "config": {
            "argument": "{query}",
            "passthroughargument": True,
            "variables": {"mode": mode},
        },
        "type": "alfred.workflow.utility.argument",
        "uid": uid(uid_name),
        "version": 1,
    }


def connection(dest: str, modifiers: int = 0, subtext: str = "") -> dict:
    return {
        "destinationuid": uid(dest),
        "modifiers": modifiers,
        "modifiersubtext": subtext,
        "vitoclose": False,
    }


def user_config() -> list[dict]:
    return [
        {
            "config": {
                "default": "p",
                "placeholder": "p",
                "required": True,
                "trim": True,
            },
            "description": "Opens Passwords and searches. ⌘↩ copies the password, ⌥↩ copies the verification code, ⌃↩ copies the user name.",
            "label": "Search keyword",
            "type": "textfield",
            "variable": "keyword_search",
        },
        {
            "config": {
                "default": "fp",
                "placeholder": "fp",
                "required": True,
                "trim": True,
            },
            "description": "Copies the password of the first Passwords result, then closes the app if that option is on.",
            "label": "Copy password keyword",
            "type": "textfield",
            "variable": "keyword_password",
        },
        {
            "config": {
                "default": "otp",
                "placeholder": "otp",
                "required": True,
                "trim": True,
            },
            "description": "Copies the verification code of the first Passwords result.",
            "label": "Copy OTP keyword",
            "type": "textfield",
            "variable": "keyword_otp",
        },
        {
            "config": {
                "default": True,
                "required": False,
                "text": "Quit Passwords after copying a password, user name, or verification code",
            },
            "description": "Leave this on to match the original workflow. Turn it off to keep the matching account open.",
            "label": "Close after copy",
            "type": "checkbox",
            "variable": "close_after_copy",
        },
    ]


def workflow_plist() -> dict:
    ids = {name: uid(name) for name in OBJECTS}
    return {
        "bundleid": BUNDLE_ID,
        "category": "Tools",
        "connections": {
            ids["kw_search"]: [
                connection("arg_find"),
                connection("arg_password", MOD_CMD, "Copy password of first result"),
                connection("arg_otp", MOD_OPT, "Copy verification code of first result"),
                connection("arg_username", MOD_CTRL, "Copy user name of first result"),
            ],
            ids["kw_password"]: [connection("arg_password")],
            ids["kw_otp"]: [connection("arg_otp")],
            ids["arg_find"]: [connection("script")],
            ids["arg_password"]: [connection("script")],
            ids["arg_otp"]: [connection("script")],
            ids["arg_username"]: [connection("script")],
        },
        "createdby": "qwertyuiop97",
        "description": "Find and copy iCloud passwords and verification codes from the Passwords app",
        "disabled": False,
        "name": "iCloud Passwords",
        "objects": [
            keyword(
                "kw_search",
                "keyword_search",
                "Find passwords",
                "Open Passwords and search · ⌘ password · ⌥ OTP · ⌃ user name",
            ),
            keyword(
                "kw_password",
                "keyword_password",
                "Copy password of first result",
                "Search Passwords, copy the first password, and quit",
            ),
            keyword(
                "kw_otp",
                "keyword_otp",
                "Copy OTP of the first result",
                "Search Passwords, copy the first verification code, and quit",
            ),
            arg_and_vars("arg_find", "find"),
            arg_and_vars("arg_password", "password"),
            arg_and_vars("arg_otp", "otp"),
            arg_and_vars("arg_username", "username"),
            {
                "config": {
                    "concurrently": False,
                    "escaping": 0,
                    "script": 'mode="${mode:-find}"\nquery="${1-}"\ntitles="$(/usr/bin/python3 ./titles.py)"\n/usr/bin/osascript ./passwords.applescript "$mode" "$query" "$titles"\n',
                    "scriptargtype": 1,
                    "scriptfile": "",
                    "type": 5,
                },
                "type": "alfred.workflow.action.script",
                "uid": ids["script"],
                "version": 2,
            },
        ],
        "readme": """# iCloud Passwords

Search Apple’s Passwords app from Alfred and copy the first matching password, user name, or verification code.

## Setup

1. Alfred 5 with Powerpack, macOS Sequoia or later (including Tahoe and Golden Gate).
2. Grant **Accessibility** to Alfred: System Settings → Privacy & Security → Accessibility.
3. The first run will open Passwords. Unlock it with Touch ID or your Mac password.

## Keywords

Defaults, all editable in Configure Workflow:

- `p <query>` — open Passwords and search
- `fp <query>` — copy the first result’s password
- `otp <query>` — copy the first result’s verification code

From `p`: **⌘↩** password, **⌥↩** OTP, **⌃↩** user name.

Independent Alfred 5 workflow for the macOS Passwords app (Sequoia, Tahoe, Golden Gate). The 2021 Safari preference-pane workflows no longer work.
""",
        "uidata": {
            ids["kw_search"]: {"xpos": 50, "ypos": 30},
            ids["kw_password"]: {"xpos": 50, "ypos": 170},
            ids["kw_otp"]: {"xpos": 50, "ypos": 310},
            ids["arg_find"]: {"xpos": 280, "ypos": 50},
            ids["arg_password"]: {"xpos": 280, "ypos": 190},
            ids["arg_otp"]: {"xpos": 280, "ypos": 330},
            ids["arg_username"]: {"xpos": 280, "ypos": 430},
            ids["script"]: {"xpos": 510, "ypos": 190},
        },
        "userconfigurationconfig": user_config(),
        "variables": {
            "keyword_search": "p",
            "keyword_password": "fp",
            "keyword_otp": "otp",
            "close_after_copy": "1",
        },
        "variablesdontexport": [],
        "version": "2.0.0",
        "webaddress": REPO_URL,
    }


WORKFLOW_FILES = (
    "info.plist",
    "passwords.applescript",
    "titles.py",
    "run.sh",
    "icon.png",
)


def write_plist() -> Path:
    path = ROOT / "info.plist"
    path.write_bytes(plistlib.dumps(workflow_plist(), fmt=plistlib.FMT_XML, sort_keys=False))
    return path


def package() -> Path:
    DIST.mkdir(exist_ok=True)
    archive = DIST / "iCloud-Passwords.alfredworkflow"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in WORKFLOW_FILES:
            path = ROOT / name
            if not path.is_file():
                raise SystemExit(f"missing {path}")
            zf.write(path, name)
    return archive


def main() -> int:
    from make_icon import main as write_icon

    write_icon()
    write_plist()
    archive = package()
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate info.plist and the installable .alfredworkflow archive."""

from __future__ import annotations

import plistlib
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
NAME = "iCloud Passwords Revamp"
BUNDLE_ID = "com.qwertyuiop97.icloud-passwords-revamp"
REPO_URL = "https://github.com/qwertyuiop97/icloud-passwords-revamp"

UIDS = {
    "filter": "scriptfilter.search",
    "action": "action.fill",
}


def uid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"alfred://{BUNDLE_ID}/{name}")).upper()


def user_config() -> list[dict]:
    return [
        {
            "config": {
                "default": "pw",
                "placeholder": "pw",
                "required": True,
                "trim": True,
            },
            "description": "Type this in Alfred, then a site, URL, or email. Results appear underneath.",
            "label": "Search keyword",
            "type": "textfield",
            "variable": "keyword_search",
        },
        {
            "config": {
                "default": True,
                "required": False,
                "text": "When the keyword is used alone, suggest logins for the current browser tab",
            },
            "description": "Uses the tab’s host (for example arizona.edu) as the first search.",
            "label": "Current tab",
            "type": "checkbox",
            "variable": "suggest_tab",
        },
        {
            "config": {
                "default": True,
                "required": False,
                "text": "On a login form, fill user name and password together",
            },
            "description": "Never pastes a password into a user name / NetID / email field.",
            "label": "Fill both fields",
            "type": "checkbox",
            "variable": "fill_both",
        },
        {
            "config": {
                "default": True,
                "required": False,
                "text": "Quit Passwords after filling or copying",
            },
            "description": "Passwords stays in the background while you search in Alfred.",
            "label": "Close after fill",
            "type": "checkbox",
            "variable": "close_after_copy",
        },
    ]


README = """# iCloud Passwords Revamp

Alfred 5 workflow for Apple’s Passwords app.

Type `pw arizona` and matching logins appear under the query. The main text is the email or user name. The subtitle is the app, website, or URL. Return fills the login form in the frontmost app.

## Setup

1. Alfred 5 with Powerpack, macOS Sequoia or later.
2. System Settings → Privacy & Security → Accessibility → Alfred.
3. Unlock Passwords with Touch ID the first time a search needs it.

## Use

- `pw` — if a browser tab is open, suggest logins for that site
- `pw arizona` — every saved email for Arizona / arizona.edu
- ↩ — fill user name then password (NetID + Password on a WebAuth page)
- ⌘↩ copy password · ⌥↩ copy verification code · ⌃↩ copy user name · ⇧↩ open in Passwords

The workflow never reads password text into its own process. Passwords.app copies the secret, and paste is blocked unless the focused field is a real password field.
"""


def workflow_plist() -> dict:
    filter_uid = uid(UIDS["filter"])
    action_uid = uid(UIDS["action"])
    return {
        "bundleid": BUNDLE_ID,
        "category": "Tools",
        "connections": {
            filter_uid: [
                {
                    "destinationuid": action_uid,
                    "modifiers": 0,
                    "modifiersubtext": "",
                    "vitoclose": False,
                }
            ]
        },
        "createdby": "qwertyuiop97",
        "description": "Search iCloud Passwords in Alfred and fill the frontmost login form",
        "disabled": False,
        "name": NAME,
        "objects": [
            {
                "config": {
                    "alfredfiltersresults": False,
                    "alfredfiltersresultsmatchmode": 0,
                    "argumenttreatemptyqueryasnil": False,
                    "argumenttrimmode": 0,
                    "argumenttype": 1,
                    "escaping": 0,
                    "keyword": "{var:keyword_search}",
                    "queuedelaycustom": 3,
                    "queuedelayimmediatelyinitially": True,
                    "queuedelaymode": 1,
                    "queuemode": 2,
                    "runningsubtext": "Searching Passwords…",
                    "script": '/usr/bin/python3 ./search.py "$1"\n',
                    "scriptargtype": 1,
                    "scriptfile": "",
                    "skipuniversalaction": True,
                    "subtext": "Site, URL, user name, or email",
                    "title": "Search iCloud Passwords",
                    "type": 5,
                    "withspace": True,
                },
                "type": "alfred.workflow.input.scriptfilter",
                "uid": filter_uid,
                "version": 3,
            },
            {
                "config": {
                    "concurrently": False,
                    "escaping": 0,
                    "script": '/usr/bin/python3 ./action.py "$1"\n',
                    "scriptargtype": 1,
                    "scriptfile": "",
                    "type": 5,
                },
                "type": "alfred.workflow.action.script",
                "uid": action_uid,
                "version": 2,
            },
        ],
        "readme": README,
        "uidata": {
            filter_uid: {"xpos": 60, "ypos": 80},
            action_uid: {"xpos": 360, "ypos": 80},
        },
        "userconfigurationconfig": user_config(),
        "variables": {
            "keyword_search": "pw",
            "suggest_tab": "1",
            "fill_both": "1",
            "close_after_copy": "1",
        },
        "variablesdontexport": [],
        "version": "3.0.0",
        "webaddress": REPO_URL,
    }


WORKFLOW_FILES = (
    "info.plist",
    "search.py",
    "action.py",
    "ui.applescript",
    "titles.py",
    "icon.png",
    "lib/__init__.py",
    "lib/fields.py",
    "lib/results.py",
    "lib/fill.py",
    "lib/bridge.py",
    "lib/inspect.py",
    "lib/tab.py",
)


def write_plist() -> Path:
    path = ROOT / "info.plist"
    path.write_bytes(plistlib.dumps(workflow_plist(), fmt=plistlib.FMT_XML, sort_keys=False))
    return path


def package() -> Path:
    DIST.mkdir(exist_ok=True)
    archive = DIST / "iCloud-Passwords-Revamp.alfredworkflow"
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

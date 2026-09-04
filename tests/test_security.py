#!/usr/bin/env python3
"""Repo and runtime safety checks. No personal vault data."""

from __future__ import annotations

import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "dist", "tests"}
CODE_SUFFIXES = {".py", ".applescript", ".sh", ".plist", ".md"}


def iter_source() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in CODE_SUFFIXES and path.is_file():
            files.append(path)
    return files


class SecurityTests(unittest.TestCase):
    def test_no_personal_paths_or_vault_counts(self):
        banned = ("bakir", "/users/bakirmousa", "879 items", "all – 879")
        for path in iter_source():
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for token in banned:
                self.assertNotIn(token, text, msg=f"{path} contains {token!r}")

    def test_python_never_prints_password_variables(self):
        for path in ROOT.rglob("*.py"):
            if ".git" in path.parts or path.name.startswith("test_"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print":
                    dumped = ast.dump(node)
                    self.assertNotIn("password", dumped.lower(), msg=f"print() in {path}")

    def test_no_pbpaste_of_secrets(self):
        for path in iter_source():
            if path.suffix not in {".py", ".applescript", ".sh"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("pbpaste", text)

    def test_ui_script_never_emits_field_value(self):
        script = (ROOT / "ui.applescript").read_text(encoding="utf-8")
        self.assertIn("Never emit the field value", script)
        self.assertNotIn("set out to out & (value of f", script)

    def test_search_path_does_not_front_passwords(self):
        swift = (ROOT / "SearchAX.swift").read_text(encoding="utf-8")
        self.assertNotIn("unhide()", swift)
        self.assertNotIn("activatePasswords", swift)
        self.assertNotIn("AXIsProcessTrustedWithOptions", swift)
        self.assertNotIn('"-g", "-a", "Passwords"', swift)
        js = (ROOT / "search_ui.js").read_text(encoding="utf-8")
        self.assertNotIn("frontmost = true", js)
        self.assertNotIn("open -g -a Passwords", js)
        self.assertNotIn("keystroke", js)
        script = (ROOT / "ui.applescript").read_text(encoding="utf-8")
        search_block = script.split('if mode is "search"')[1].split('if mode is "inspect"')[0]
        self.assertNotIn("launchPasswordsHidden", search_block)
        self.assertNotIn("raisePasswordsForAX", search_block)
        self.assertNotIn("clickUnlock", search_block)
        self.assertNotIn("keystroke", search_block)
        self.assertNotIn("launchPasswordsHidden", search_block)

    def test_no_unconditional_browser_tells(self):
        script = (ROOT / "ui.applescript").read_text(encoding="utf-8")
        self.assertNotIn('tell application "Brave Browser"', script)
        self.assertNotIn('if application "Brave Browser" is running', script)
        self.assertIn("frontContext", script)

    def test_search_json_fixture_has_no_password_key(self):
        from lib.results import item_payload
        import json

        item = item_payload({"title": "example.com", "username": "user@example.com"})
        raw = json.dumps(item)
        self.assertNotIn('"password"', raw)
        self.assertIn("user@example.com", item["title"])


if __name__ == "__main__":
    unittest.main()

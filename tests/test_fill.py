#!/usr/bin/env python3
"""Fill steps never send a password to a username field."""

from __future__ import annotations

import unittest

from lib.fill import parse_account, steps_for


WEBFORM = [
    {
        "role": "AXTextField",
        "subrole": "AXTextField",
        "name": "NetID",
        "focused": True,
    },
    {
        "role": "AXTextField",
        "subrole": "AXSecureTextField",
        "name": "Password",
        "focused": False,
    },
]


class FillTests(unittest.TestCase):
    def test_account_rejects_secrets(self):
        with self.assertRaises(ValueError):
            parse_account('{"title":"x","username":"a","password":"nope"}')

    def test_webauth_enter_fills_username_then_password(self):
        steps = steps_for("fill", WEBFORM)
        self.assertEqual([s["menu"] for s in steps], ["username", "password"])
        self.assertEqual(steps[0]["paste"], "username")
        self.assertEqual(steps[1]["paste"], "password")
        self.assertEqual(steps[1].get("clear"), "yes")

    def test_password_paste_is_never_first_on_a_login_form(self):
        steps = steps_for("fill", WEBFORM)
        self.assertEqual(steps[0]["paste"], "username")

    def test_copy_password_does_not_paste(self):
        steps = steps_for("copy_password", WEBFORM)
        self.assertEqual(steps, [{"menu": "password", "paste": "none", "conceal": "yes"}])

    def test_fill_both_off_uses_focused_netid_only(self):
        steps = steps_for("fill", WEBFORM, fill_both=False)
        self.assertEqual(steps, [{"menu": "username", "paste": "username"}])

    def test_no_fields_does_not_blind_paste_password(self):
        steps = steps_for("fill", [])
        self.assertEqual(steps[0]["menu"], "username")
        self.assertEqual(steps[0]["paste"], "none")

    def test_close_after_copy_defaults_off_in_action(self):
        from pathlib import Path

        text = Path(__file__).resolve().parent.parent.joinpath("action.py").read_text()
        self.assertIn('os.environ.get("close_after_copy") or "0"', text)
        self.assertNotIn('os.environ.get("close_after_copy") or "1"', text)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Field classification and fill-plan safety. Fixtures only, no real logins."""

from __future__ import annotations

import unittest

from lib.fields import (
    is_password_field,
    is_username_field,
    may_receive_password,
    may_receive_username,
    plan_fill,
)

NETID = {
    "role": "AXTextField",
    "subrole": "AXTextField",
    "name": "NetID",
    "placeholder": "",
    "focused": True,
}
PASSWORD = {
    "role": "AXTextField",
    "subrole": "AXSecureTextField",
    "name": "Password",
    "placeholder": "",
    "focused": False,
}
EMAIL = {
    "role": "AXTextField",
    "name": "Email",
    "placeholder": "you@example.com",
    "focused": False,
}
COMMENT = {
    "role": "AXTextArea",
    "name": "Comments",
    "focused": True,
}


class FieldTests(unittest.TestCase):
    def test_netid_is_username_not_password(self):
        self.assertTrue(is_username_field(NETID))
        self.assertFalse(is_password_field(NETID))
        self.assertTrue(may_receive_username(NETID))
        self.assertFalse(may_receive_password(NETID))

    def test_secure_field_is_password_only(self):
        self.assertTrue(is_password_field(PASSWORD))
        self.assertFalse(is_username_field(PASSWORD))
        self.assertTrue(may_receive_password(PASSWORD))
        self.assertFalse(may_receive_username(PASSWORD))

    def test_webauth_form_fills_both(self):
        plan = plan_fill([NETID, PASSWORD])
        self.assertEqual(plan.mode, "both")
        self.assertEqual(plan.username_field["name"], "NetID")
        self.assertEqual(plan.password_field["name"], "Password")
        plan.validate()

    def test_password_only_form(self):
        plan = plan_fill([{**PASSWORD, "focused": True}])
        self.assertEqual(plan.mode, "password")
        self.assertIsNone(plan.username_field)

    def test_username_only_form(self):
        plan = plan_fill([EMAIL])
        self.assertEqual(plan.mode, "username")
        self.assertIsNone(plan.password_field)

    def test_never_plan_password_into_netid(self):
        plan = plan_fill([NETID, PASSWORD])
        self.assertFalse(may_receive_password(plan.username_field))
        self.assertTrue(may_receive_password(plan.password_field))

    def test_comment_plus_password_does_not_treat_comment_as_username(self):
        plan = plan_fill([COMMENT, PASSWORD])
        self.assertEqual(plan.mode, "password")
        self.assertIsNone(plan.username_field)

    def test_validate_rejects_swapped_fields(self):
        from lib.fields import FillPlan

        with self.assertRaises(ValueError):
            FillPlan("both", PASSWORD, NETID).validate()


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Search display and matching. Example.com fixtures only."""

from __future__ import annotations

import json
import unittest

from lib.results import (
    filter_items,
    haystack,
    item_payload,
    matches,
    parse_search_output,
)
from lib.tab import host_from_url, search_query_from_url

ARIZONA_A = {"title": "arizona.edu", "username": "netid@arizona.edu"}
ARIZONA_B = {"title": "WebAuth", "username": "other@arizona.edu"}
GITHUB = {"title": "GitHub", "username": "alice@example.com", "url": "https://github.com/login"}


class ResultTests(unittest.TestCase):
    def test_locked_status_keeps_alfred_open(self):
        from lib.results import status_item

        item = status_item("LOCKED")
        self.assertFalse(item["valid"])
        self.assertIn("Leave this window open", item["subtitle"])
        self.assertEqual(item["rerun"], 0.8)

    def test_empty_query_does_not_list_vault(self):
        items = filter_items("", [ARIZONA_A, ARIZONA_B, GITHUB])
        self.assertEqual(len(items), 1)
        self.assertFalse(items[0]["valid"])

    def test_arizona_returns_every_matching_email(self):
        items = filter_items("arizona", [ARIZONA_A, ARIZONA_B, GITHUB])
        emails = {item["title"] for item in items}
        self.assertEqual(emails, {"netid@arizona.edu", "other@arizona.edu"})

    def test_row_title_is_email_subtitle_is_site(self):
        item = item_payload(ARIZONA_A)
        self.assertEqual(item["title"], "netid@arizona.edu")
        self.assertEqual(item["subtitle"], "arizona.edu")
        payload = json.loads(item["arg"])
        self.assertNotIn("password", payload)
        self.assertEqual(payload["username"], "netid@arizona.edu")

    def test_search_by_email_local_part(self):
        self.assertTrue(matches(ARIZONA_A, "netid"))
        self.assertTrue(matches(ARIZONA_A, "netid@arizona.edu"))
        self.assertFalse(matches(GITHUB, "netid"))

    def test_search_by_url_host(self):
        self.assertTrue(matches(GITHUB, "github.com"))
        self.assertTrue(matches(GITHUB, "github"))
        self.assertTrue("github" in haystack(GITHUB))

    def test_parse_skips_masked_and_sidebar(self):
        raw = "OK\nAll\t\nGitHub\talice@example.com\n••••••••\thidden\n"
        status, rows = parse_search_output(raw)
        self.assertEqual(status, "OK")
        self.assertEqual(rows, [{"title": "GitHub", "username": "alice@example.com"}])

    def test_copy_text_is_username_not_a_password(self):
        item = item_payload(ARIZONA_A)
        self.assertEqual(item["text"]["copy"], "netid@arizona.edu")
        dumped = json.dumps(item)
        self.assertNotIn("secret", dumped.lower())

    def test_tab_url_to_arizona_query(self):
        url = "https://webauth.arizona.edu/webauth/login"
        self.assertEqual(host_from_url(url), "webauth.arizona.edu")
        self.assertEqual(search_query_from_url(url), "arizona.edu")


if __name__ == "__main__":
    unittest.main()

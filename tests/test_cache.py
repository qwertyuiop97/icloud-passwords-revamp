#!/usr/bin/env python3
"""Cache must not mask a locked vault."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.cache import invalidate, local_hits, save


class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"alfred_workflow_cache": self.tmp.name})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.tmp.cleanup()

    def test_prefix_narrows_after_live_save(self) -> None:
        save(
            "ari",
            [
                {"title": "arizona.edu", "username": "netid@arizona.edu"},
                {"title": "GitHub", "username": "alice@example.com"},
            ],
        )
        hits = local_hits("arizona")
        self.assertIsNotNone(hits)
        assert hits is not None
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["title"], "arizona.edu")

    def test_invalidate_drops_hits(self) -> None:
        save("ari", [{"title": "arizona.edu", "username": "netid@arizona.edu"}])
        invalidate()
        self.assertIsNone(local_hits("arizona"))
        self.assertFalse((Path(self.tmp.name) / "meta.json").is_file())


def _run_main(query: str) -> str:
    import io
    from contextlib import redirect_stdout
    import search

    buf = io.StringIO()
    with redirect_stdout(buf):
        search.main(["search.py", query])
    return buf.getvalue()


class SearchMainTests(unittest.TestCase):
    def test_locked_probe_does_not_emit_cached_logins(self) -> None:
        import search

        cached = [{"title": "arizona.edu", "username": "netid@arizona.edu"}]
        with patch.object(search, "probe_vault", return_value="LOCKED"), patch.object(
            search, "local_hits", return_value=cached
        ) as hits, patch.object(search, "invalidate") as inv, patch.object(
            search, "bridge_search", side_effect=AssertionError("live search must not run")
        ):
            raw = _run_main("arizona")
        payload = json.loads(raw)
        items = payload["items"]
        self.assertEqual(len(items), 1)
        self.assertIn("Unlock", items[0]["title"])
        self.assertNotEqual(items[0]["title"], "netid@arizona.edu")
        inv.assert_called()
        hits.assert_not_called()

    def test_unlocked_cache_is_marked(self) -> None:
        import search

        cached = [{"title": "arizona.edu", "username": "netid@arizona.edu"}]
        with patch.object(search, "probe_vault", return_value="UNLOCKED"), patch.object(
            search, "local_hits", return_value=cached
        ), patch.object(
            search, "bridge_search", side_effect=AssertionError("live search skipped when cache hits")
        ):
            raw = _run_main("arizona")
        payload = json.loads(raw)
        item = payload["items"][0]
        self.assertEqual(item["title"], "netid@arizona.edu")
        self.assertIn("cached", item["subtitle"])
        self.assertEqual(item["variables"].get("source"), "cache")


if __name__ == "__main__":
    unittest.main()

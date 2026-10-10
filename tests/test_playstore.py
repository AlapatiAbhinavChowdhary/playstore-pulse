"""Parsers are tested against responses recorded from the live Play Store on 10 Oct 2026
(reviewer names scrubbed). The fetch loop is tested against a local server replaying them."""
import http.server
import os
import threading
import unittest

from pulse import playstore, store

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class Parsers(unittest.TestCase):
    def test_reviews_response(self):
        rows, token = playstore.parse_reviews_response(_read("reviews_response.txt"))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["stars"], 5)
        self.assertEqual(rows[0]["text"], "good")
        self.assertEqual(rows[0]["app_version"], "10.2.1")
        self.assertGreater(rows[0]["at_epoch"], 1_700_000_000)
        self.assertTrue(token and token.startswith("Ctc"))
        self.assertNotIn("userName", rows[0])            # we never keep who wrote it

    def test_listing(self):
        d = playstore.parse_listing(_read("listing_snippet.html"))
        self.assertEqual(d["title"], "Moveinsync Partner - Lite")
        self.assertAlmostEqual(d["score"], 4.29)
        self.assertEqual(d["histogram"], [84, 21, 21, 56, 518])
        self.assertEqual(sum(d["histogram"]), 700)
        self.assertEqual(d["installs"], 143072)

    def test_listing_survives_a_changed_page(self):
        d = playstore.parse_listing("<html>nothing useful</html>")
        self.assertIsNone(d["score"])
        self.assertIsNone(d["histogram"])


class _Replay(http.server.BaseHTTPRequestHandler):
    posts = 0

    def log_message(self, *a):
        pass

    def do_GET(self):
        body = _read("listing_snippet.html").encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        type(self).posts += 1
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = _read("reviews_response.txt").encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)


class FetchLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Replay)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.old = playstore.BASE
        playstore.BASE = f"http://127.0.0.1:{cls.srv.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        playstore.BASE = cls.old
        cls.srv.shutdown()

    def test_listing_over_http(self):
        d = playstore.fetch_listing("com.moveinsync.driver.lite")
        self.assertEqual(d["app_id"], "com.moveinsync.driver.lite")
        self.assertEqual(d["ratings"], 701)

    def test_incremental_fetch_stops_when_nothing_is_new(self):
        _Replay.posts = 0
        first = list(playstore.fetch_reviews("x", max_pages=2, pause=0))
        self.assertEqual(len(first), 6)                  # the replay always has a next-page token: 2 pages x 3
        _Replay.posts = 0
        known = frozenset(r["review_id"] for r in first)
        again = list(playstore.fetch_reviews("x", known_ids=known, max_pages=50, pause=0))
        self.assertEqual(_Replay.posts, 1)               # one page, all known, stop
        self.assertEqual(len(again), 3)

    def test_merge_is_idempotent_and_picks_up_edits(self):
        import tempfile
        rows, _ = playstore.parse_reviews_response(_read("reviews_response.txt"))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "reviews.csv")
            self.assertEqual(store.merge_reviews(path, "app", rows), (3, 0))
            self.assertEqual(store.merge_reviews(path, "app", rows), (0, 0))
            rows[0]["stars"] = 1                         # the reviewer came back and changed their mind
            self.assertEqual(store.merge_reviews(path, "app", rows), (0, 1))
            saved = store.read_rows(path)
            self.assertEqual(len(saved), 3)
            self.assertIn("1", {r["stars"] for r in saved})
            self.assertTrue(all(r["reviewed_at_ist"] for r in saved))


class Privacy(unittest.TestCase):
    def test_reply_greetings_lose_the_name_and_nothing_else(self):
        self.assertEqual(playstore.scrub_reply("Hi Asha, We have fixed this in 12.20"), "Hi, We have fixed this in 12.20")
        self.assertEqual(playstore.scrub_reply("Hi, could you please share details"), "Hi, could you please share details")
        self.assertEqual(playstore.scrub_reply("Hi, We are sorry to hear that"), "Hi, We are sorry to hear that")
        self.assertEqual(playstore.scrub_reply(""), "")


if __name__ == "__main__":
    unittest.main()

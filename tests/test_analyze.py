"""Small synthetic corpus: checks the arithmetic the report depends on."""
import unittest

from pulse import analyze, digest, plan


def _rev(i, day, stars, text, version="1.0", reply_day=None):
    return {"app_id": "com.moveinsync.ets", "review_id": f"r{i}", "reviewed_at_ist": f"2026-09-{day:02d} 10:00:00", "stars": str(stars),
            "thumbs_up": "0", "app_version": version, "replied_at_ist": f"2026-09-{reply_day:02d} 12:00:00" if reply_day else "",
            "text": text, "reply_text": "Thanks, fixed in the next version" if reply_day else "", "lang": "en"}


REVIEWS = ([_rev(i, 1 + i % 28, 5, "good") for i in range(60)]
           + [_rev(100 + i, 1 + i % 28, 1, "not receiving the otp, cannot login") for i in range(20)]
           + [_rev(200 + i, 21 + i, 1, "cab was 40 minutes late") for i in range(10)]
           + [_rev(300, 5, 2, "worst app"), _rev(301, 20, 1, "crashes on open", reply_day=21), _rev(302, 20, 1, "crashes again", reply_day=3)])
SNAPS = [{"date": "2026-09-01", "app_id": "com.moveinsync.ets", "country": "IN", "title": "MoveInSync", "score": "4.60", "ratings": "1000", "reviews": "90",
          "h1": "70", "h2": "10", "h3": "10", "h4": "60", "h5": "850", "installs": "1", "version": "1.0"},
         {"date": "2026-09-30", "app_id": "com.moveinsync.ets", "country": "IN", "title": "MoveInSync", "score": "4.59", "ratings": "1100", "reviews": "93",
          "h1": "90", "h2": "10", "h3": "10", "h4": "60", "h5": "930", "installs": "1", "version": "1.0"},
         {"date": "2026-09-30", "app_id": "com.ubercab", "country": "IN", "title": "Uber", "score": "4.73", "ratings": "1000", "reviews": "10",
          "h1": "40", "h2": "10", "h3": "10", "h4": "60", "h5": "880", "installs": "1", "version": ""}]


class Analyze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = analyze.analyze(REVIEWS, [], SNAPS, today="2026-09-30", validate=False)

    def test_windows(self):
        w = self.m["windows"]["last_30d"]
        self.assertEqual(w["n"], 93)
        self.assertAlmostEqual(w["mean"], (60 * 5 + 32 * 1 + 2) / 93, places=3)

    def test_owner_split_ignores_reviews_without_a_reason(self):
        o = self.m["owners"]["last_30d"]
        self.assertAlmostEqual(o["gives_reason"], 32 / 33, places=2)        # "worst app" gives none
        self.assertAlmostEqual(o["app_side"], 22 / 32, places=2)            # 20 login + 2 crash
        self.assertAlmostEqual(o["ride_only"], 10 / 32, places=2)

    def test_a_reply_older_than_the_review_does_not_count(self):
        r = self.m["replies"]["last_12m"]
        self.assertEqual(r["low_star"], 33)
        self.assertEqual(r["low_star_unanswered"], 32)                       # only r301 was answered after it was written
        self.assertEqual(r["stale"], 1)

    def test_flow_between_snapshots(self):
        f = self.m["flow"]
        self.assertTrue(f["valid"])
        self.assertEqual(f["new_ratings"], 100)
        self.assertAlmostEqual(f["one_share"], 0.2)
        self.assertAlmostEqual(f["mean"], (20 * 1 + 80 * 5) / 100)

    def test_peer_level_score_is_higher_than_today(self):
        p = self.m["layers"]["peer_level"]
        self.assertGreater(p["score_at_peer_level"], self.m["listing"]["score"])

    def test_impact_never_promises_more_than_it_removes(self):
        scen = self.m["impact"]
        self.assertEqual([s["scenario"] for s in scen], ["This week", "Plus next 30 days", "Whole plan"])
        scores = [s["score"] for s in scen]
        self.assertEqual(scores, sorted(scores))
        self.assertLessEqual(scen[-1]["low_star_avoided_per_year"], scen[-1]["of"])

    def test_plan_evidence_counts_unique_reviews(self):
        a1 = next(a for a in self.m["plan"] if a["id"] == "A1")
        self.assertEqual(a1["evidence"]["n"], 2)                             # the two crash reviews
        b1 = next(a for a in self.m["plan"] if a["id"] == "B1")
        self.assertEqual(b1["evidence"]["window"], "last_12m")               # no reference tags here, so it falls back
        self.assertEqual(b1["evidence"]["n"], 20)

    def test_digest_flags_the_flow_and_the_unanswered(self):
        text = digest.render(self.m)
        self.assertIn("Public score 4.59", text)
        owners = {a["owner"] for a in digest.alerts(self.m)}
        self.assertIn("Support lead", owners)
        self.assertIn("Product manager", owners)                             # 20% of new ratings are 1-star vs 8% on the listing

    def test_every_action_has_the_four_parts(self):
        for a in plan.ACTIONS:
            for k in ("why", "do", "tomorrow", "done_when", "owner"):
                self.assertTrue(a[k], (a["id"], k))


if __name__ == "__main__":
    unittest.main()

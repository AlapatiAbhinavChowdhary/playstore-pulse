"""Each case is a real complaint pattern, reduced to its essentials."""
import unittest

from pulse import taxonomy as T
from pulse.classify import RuleClassifier

CASES = [
    ("after 2 days it says cannot open as not installed from play store", "install_integrity"),
    ("every day I have to uninstall and install it again to make it work", "install_integrity"),
    ("app keeps crashing on my phone", "launch_crash"),
    ("not receiving the OTP on mobile or email", "login_otp"),
    ("it logs me out every five minutes", "login_otp"),
    ("the map never updates the cab location", "tracking_eta"),
    ("unable to cancel my booking before the cut off", "booking_schedule"),
    ("after the new update everything is harder", "update_regression"),
    ("forcing me to give rating after every ride with no skip option", "forced_rating"),
    ("no option to rate previous trips", "trip_feedback"),
    ("why does it need microphone permission", "permissions_privacy"),
    ("cab came 40 minutes late and they marked me no show", "cab_late_noshow"),
    ("worst routing, 2 hours to reach home", "routing_pickup"),
    ("helpdesk never picks up the call", "support_channel"),
    ("driver was rude and abusive", "driver_vehicle"),
]


class Rules(unittest.TestCase):
    def test_known_patterns(self):
        for text, want in CASES:
            with self.subTest(text=text):
                self.assertIn(want, T.classify(text))

    def test_login_trip_is_not_a_login_problem(self):
        # In this product "login trip" means the ride to the office.
        self.assertNotIn("login_otp", T.classify("my login cab was late by an hour"))

    def test_vague_reviews_fall_back(self):
        self.assertEqual(T.classify("worst app"), ["generic"])
        self.assertEqual(T.classify(""), ["generic"])

    def test_specific_beats_vague(self):
        self.assertNotIn("app_unstable", T.classify("app not working, it crashes every time I open tracking"))

    def test_every_theme_has_an_owner_and_a_label(self):
        for k in T.ORDER:
            self.assertIn(k, T.OWNER)
            self.assertIn(k, T.LABEL)

    def test_rule_classifier_shape(self):
        out = RuleClassifier().predict(["otp not coming", "good"])
        self.assertEqual(len(out), 2)
        self.assertTrue(all(isinstance(x, list) and x for x in out))


if __name__ == "__main__":
    unittest.main()

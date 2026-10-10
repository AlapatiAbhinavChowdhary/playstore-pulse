"""The recommendation, as data.

Each action names the themes it answers. Evidence counts are filled in from the
live metrics at render time, so the plan and the numbers can never drift apart:
re-run the pulse and the same page tells you whether an action is working.

`avoidable` is the share of reviews carrying only these themes that we expect
the action to prevent. They are stated assumptions, not measurements - change
them here and the impact estimate on the page changes with them.
"""

ACTIONS = [
    {
        "id": "A1", "phase": "This week", "owner": "Android lead",
        "title": "Hotfix the \"not installed from Play Store\" lock-out and the launch crashes",
        "themes": ["install_integrity", "launch_crash"], "avoidable": 0.8, "evidence_window": "last_90d",
        "why": "A new failure is live right now. From March 2025 to May 2026 this lock-out was almost absent; since versions 12.16 to 12.19 "
               "it is back, and together with launch crashes it is the largest current reason for a low rating. People say the app claims "
               "it was not installed from Play Store, refuses to open, and only a reinstall brings it back, until it happens again a few "
               "days later. Several say it starts two to three days after an install or update, which points at a cached verdict or licence "
               "check expiring rather than at the install itself. Reviewers name OnePlus 12, Pixel 8 on Android 17, Vivo V25 Pro and Samsung S22+.",
        "do": [
            "Open Play Console > Android vitals. Pull crash and ANR clusters for 12.16.0 to 12.20.0, split by Android version and device model.",
            "Find the installer-source / Play Integrity check behind that error text. Make it fail open: on a failed or inconclusive verdict, retry in the background and let the user in. Log the verdict to the server; never block and never ask for a reinstall.",
            "Test the auto-update path (update while logged in, then cold start) on Android 15, 16 and 17.",
            "Ship as a staged rollout: 10% > 50% > 100%, halting if crash-free sessions drop under 99.5%.",
            "Reply to every reviewer who reported it with the version that fixes it.",
        ],
        "tomorrow": "Run: python -m pulse show install_integrity --since 2026-06-01. That prints the repro list: dates, versions, devices, the user's own words. Then reproduce by updating 12.15 to 12.19 through Play on a Pixel 8.",
        "done_when": "No new review in this theme for 30 days, and crash-free users at or above 99.5% on the newest Android version.",
    },
    {
        "id": "A2", "phase": "This week", "owner": "Support lead",
        "title": "Answer every 1 to 3 star review within 24 hours",
        "themes": [], "avoidable": 0.0, "evidence_window": "last_12m",
        "why": "The team used to do this and stopped. In 2023 almost every review got a reply, typically within 15 hours. Since July 2024 "
               "almost none do. The few replies still going out are short templates. A brief restart in late 2025 answered about eighty reviews and lapsed, which says this needs an owner "
               "and a queue, not a campaign. Google's own figure is that replying to a negative review lifts that rating by 0.7 stars on average, and it costs no engineering time.",
        "do": [
            "Name one owner and a daily 15-minute queue. The weekly digest lists every unanswered low-star review.",
            "Write eight reply templates, one per major theme, that (1) name the specific problem, (2) say what the user can do today, (3) say which version fixes it. Retire \"please contact your transport manager\" as a standalone answer.",
            "When a fix ships, reply again on the reviews that reported that problem. Play notifies the reviewer and invites them to update the rating.",
            "Later: draft replies automatically from the theme and have a person approve them through the Play Developer Reply API.",
        ],
        "tomorrow": "Two people, one day: reply to the low-star reviews of the last 90 days, lock-out and login first because there is a concrete workaround to give.",
        "done_when": "95% of low-star reviews answered within 24 hours, every week.",
    },
    {
        "id": "A3", "phase": "This week", "owner": "Product manager, rider app",
        "title": "Let people skip the trip rating, and stop asking for Play reviews after every ride",
        "themes": ["forced_rating", "trip_feedback"], "avoidable": 0.8, "evidence_window": "last_12m",
        "why": "This is the one complaint that is literally about ratings. People write that they came to give one star because the app "
               "would not let them see their next cab until they rated the last one. Others report the opposite problem: no way to rate or "
               "report a bad trip later, and a form that only accepts 4 or 5 stars. Both break trust in the number.",
        "do": [
            "Add Skip. Never put trip details, the boarding OTP or tracking behind a rating screen.",
            "Accept all five stars with reason chips, and allow rating or reporting a trip from trip history for 48 hours.",
            "Ask for a Play Store review only through Google's In-App Review API, after an objectively good trip (on-time pickup, no issue raised), at most once a quarter per person. Remove custom \"rate us\" pop-ups.",
        ],
        "tomorrow": "If the rating wall is server-configured, switch it off behind a flag today. Then verify the reports of low stars being rejected - if true, fix it before anything else on this list.",
        "done_when": "No new review in this theme for 30 days; in-app trip-rating response rate holds within 10% of today.",
    },
    {
        "id": "B1", "phase": "Next 30 days", "owner": "Platform / auth team",
        "title": "Make sessions last and OTPs arrive",
        "themes": ["login_otp"], "avoidable": 0.7, "evidence_window": "labelled",
        "why": "Getting logged out, or not getting the OTP, is the single biggest named reason for a low rating. It arrives in bursts that "
               "follow releases: January-February 2025, June 2025 and October 2025 each brought three to four times the usual monthly count. "
               "A commuter standing at a pickup point at 4 a.m. who cannot log in cannot see the cab number, the driver or the boarding OTP.",
        "do": [
            "Refresh-token sessions that survive restarts, network drops and app updates. Re-authenticate at most every 30 days, or as the customer's SSO policy requires.",
            "Never log out on a failed network call. Reviews describe being logged out by a tunnel or a basement car park.",
            "OTP delivery with failover - SMS, WhatsApp, email, voice call - and a delivery-rate dashboard by provider and customer, with alerts.",
            "Say plainly when a phone number or email is not registered instead of sending nothing.",
            "Offline trip card: cache the next trip (cab number, driver, pickup time, boarding OTP) so a logged-out or offline user can still board.",
            "Add login success rate to the release gate.",
        ],
        "tomorrow": "Pull auth logs for the three incident windows: attempts versus successes by app version and customer. Find the session-expiry change that shipped around 13 June 2025.",
        "done_when": "Login success at or above 99.5%, OTP delivered within 30 seconds at the 95th percentile, and this theme under 5% of low-star reviews.",
    },
    {
        "id": "B2", "phase": "Next 30 days", "owner": "Release manager / QA",
        "title": "Gate releases on the signals that produce 1-star reviews",
        "themes": ["update_regression", "app_unstable"], "avoidable": 0.5, "evidence_window": "last_12m",
        "why": "The app ships roughly every two weeks, and the share of 1-star reviews swings widely from one release to the next. "
               "The Play listing's \"What's new\" is empty, so users discover changes by surprise. Each bad release is visible in this data within days.",
        "do": [
            "Staged rollout for every release with automatic halt criteria: crash-free sessions, login success, and the 1-star share from this pulse.",
            "Test matrix that includes the next Android version before it ships, and the ten most-used devices.",
            "UI changes behind flags, offered first as an opt-in beta to two or three customers.",
            "Write real release notes on Play for every release.",
            "Run the pulse daily for seven days after each release.",
        ],
        "tomorrow": "Add the release table from this page to the release checklist, and write \"What's new\" for the build going out now.",
        "done_when": "No release with a 1-star share more than 8 points above the trailing baseline.",
    },
    {
        "id": "B3", "phase": "Next 30 days", "owner": "Product + customer operations",
        "title": "Give ride complaints a home inside the app",
        "themes": ["routing_pickup", "cab_late_noshow", "driver_vehicle", "support_channel", "service_vendor"], "avoidable": 0.3, "evidence_window": "last_12m",
        "why": "About one low-star review in five is about the ride, not the app: a late cab, a long route, a rude driver, a no-show marked "
               "unfairly, a helpdesk that does not pick up. Several say outright they are writing on Play Store because there is nowhere else. "
               "The app cannot fix a late cab, but it can make sure the complaint reaches someone who can.",
        "do": [
            "\"Report a problem with this trip\" on the trip card and in history: late, wrong route, driver, no-show dispute, safety.",
            "Route it to the customer's transport desk with an SLA timer, and show the employee the status.",
            "No-show disputes carry the GPS trail automatically, so the decision is quick and fair.",
            "When the helpdesk line is busy, offer a callback instead of a dead end.",
            "Show booking rules in the app where they bite (\"bookings close 8 hours before the shift, set by your employer\").",
        ],
        "tomorrow": "List the feedback endpoints that already exist, agree the five categories, and mock the entry point on trip history.",
        "done_when": "Ride-only complaints fall below 12% of low-star reviews; median first response on a trip issue under 30 minutes.",
    },
    {
        "id": "B4", "phase": "Next 30 days", "owner": "Maps / tracking team",
        "title": "Make live tracking believable",
        "themes": ["tracking_eta", "contact_driver"], "avoidable": 0.5, "evidence_window": "last_12m",
        "why": "Tracking is what people open the app for, and it is the subject four and five-star reviewers mention most. The complaints "
               "are consistent: the map zooms out on its own every few seconds, the cab icon sits still for minutes, the ETA jumps from "
               "5 minutes to 30, and the call-driver button does not connect.",
        "do": [
            "Stop resetting the zoom after the user has zoomed in. The smallest change on this list and one of the most cited.",
            "Show how old the position is (\"updated 40s ago\") and grey out a stale cab instead of showing a wrong one.",
            "Smooth the ETA, and show how many pickups remain before mine.",
            "Push \"cab is 5 minutes away\" and \"cab has arrived\" with sound.",
            "Detect a driver app that has been force-stopped (no heartbeat) and tell the rider and the transport desk.",
            "Fix call-driver, and add quick messages for when a call cannot connect.",
        ],
        "tomorrow": "Ship the zoom fix.",
        "done_when": "Tracking under 5% of low-star reviews; ETA within 5 minutes for 80% of pickups.",
    },
    {
        "id": "C1", "phase": "60 to 90 days", "owner": "Product design",
        "title": "Pay back the redesign debt",
        "themes": ["ui_ux", "trip_info", "booking_schedule"], "avoidable": 0.4, "evidence_window": "last_12m",
        "why": "Reviewers say the new interface removed or hid things they relied on: who else is in the cab and in what order, the pickup time, "
               "the shuttle's position. They also report that booking a shuttle became two steps, that times show no AM or PM, and that editing a booking means cancelling it first.",
        "do": [
            "Put co-riders, pickup order and pickup time back on the trip card.",
            "Show AM/PM or a 24-hour clock everywhere a time appears.",
            "One-step shuttle booking, and edit a booking without cancelling it.",
            "Dark mode, and a way to message the driver.",
        ],
        "tomorrow": "Run: python -m pulse show trip_info --since 2026-01-01. It is a short list of things people ask to have back, in their words.",
        "done_when": "Redesign and usability under 5% of low-star reviews.",
    },
    {
        "id": "C2", "phase": "60 to 90 days", "owner": "Product manager, rider app",
        "title": "Remove the forced asks",
        "themes": ["permissions_privacy", "notifications", "performance"], "avoidable": 0.5, "evidence_window": "last_12m",
        "why": "Small frictions reviewers keep naming: the transport policy to accept on every launch, microphone permission demanded up front, a forced "
               "automatic time zone, full-screen banners before the cab details, the same notification ten times a day, and a slow cold start.",
        "do": [
            "Ask for policy acceptance once per policy version, not once per launch.",
            "Ask for the microphone only when a call starts. Do not require automatic time zone.",
            "Notification preferences, and one notification per event.",
            "No full-screen banner before trip details. Set a cold-start budget of 2 seconds to the trip card.",
        ],
        "tomorrow": "Count the taps between opening the app and seeing the cab number on a fresh install.",
        "done_when": "These themes under 5% of low-star reviews combined.",
    },
    {
        "id": "C3", "phase": "60 to 90 days", "owner": "Driver-app product manager",
        "title": "Fix the small listings, where a handful of reviews decides the score",
        "themes": [], "avoidable": 0.0, "evidence_window": "last_12m",
        "why": "The driver onboarding app is rated on a few dozen ratings, the field app on fewer. Drivers report being stuck \"in review\" "
               "with no contact, and being unable to upload documents. With so few ratings, fixing and answering a dozen reviews moves the number. "
               "The same app also shows a lower score outside India, where few people have rated it.",
        "do": [
            "Show onboarding status and the expected wait in the driver app; fix document upload.",
            "Reply to every review on the three small listings - there are fewer than 130 in total.",
            "Track the US, Philippines and UK scores in the weekly digest.",
        ],
        "tomorrow": "Reply to the seven written reviews on the Driver Partner listing.",
        "done_when": "Driver Partner listing at 4.0 or above.",
    },
]


def evidence(action, metrics):
    """Count the low-star reviews an action answers, in the window it names (unique reviews)."""
    win = action["evidence_window"]
    if not metrics["low_star"][win]["n"]:        # e.g. no reference tags yet: fall back to the last 12 months
        win = "last_12m"
    total = metrics["low_star"][win]["n"]
    if not action["themes"]:
        return {"window": win, "n": None, "of": total, "share": None}
    key = "+".join(sorted(action["themes"]))
    n = metrics["action_counts"][win].get(key)
    return {"window": win, "n": n, "of": total, "share": round(n / total, 3) if total else None}


def impact(metrics, low_rows):
    """Scenario estimate for the public score once the actions have landed.

    low_rows: (stars, themes) for every low-star review of the last 12 months.
    A review is counted as avoided only to the extent that every specific complaint in it is addressed
    (the weakest link decides). Reviews that give no reason move at half the average rate.
    """
    frac = {}
    for a in ACTIONS:
        for t in a["themes"]:
            frac[t] = max(frac.get(t, 0), a["avoidable"])
    scen = {"This week": {"A1", "A3"}, "Plus next 30 days": {"A1", "A3", "B1", "B2", "B3", "B4"}, "Whole plan": {a["id"] for a in ACTIONS}}
    listing = metrics["listing"]
    h = listing["histogram"]
    n, s = sum(h), sum((i + 1) * x for i, x in enumerate(h))
    out = []
    for name, ids in scen.items():
        live = {t: a["avoidable"] for a in ACTIONS if a["id"] in ids for t in a["themes"]}
        specific, vague = [], []
        for stars, themes in low_rows:
            th = [t for t in themes if t not in ("generic", "other", "positive_text")]
            (specific if th else vague).append((stars, min(live.get(t, 0.0) for t in th) if th else None))
        avoided_spec = sum(p for _, p in specific)
        rate = avoided_spec / len(specific) if specific else 0
        avoided = avoided_spec + 0.5 * rate * len(vague)
        one = sum(p for st, p in specific if st == 1) + 0.5 * rate * sum(1 for st, _ in vague if st == 1)
        one_total = sum(1 for st, _ in low_rows if st == 1)
        cut = one / one_total if one_total else 0
        remove = h[0] * cut                     # steady state: the public 1-star count shrinks in the same proportion
        out.append({"scenario": name, "low_star_avoided_per_year": int(round(avoided)), "of": len(low_rows),
                    "one_star_cut": round(cut, 3), "one_star_share": round((h[0] - remove) / (n - remove), 4),
                    "score": round((s - remove) / (n - remove), 3)})
    return out

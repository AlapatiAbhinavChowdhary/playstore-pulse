"""What to watch. Edit this file to point the pulse at different apps."""

PRIMARY = "com.moveinsync.ets"

APPS = {
    "com.moveinsync.ets": "MoveInSync (employee app)",
    "com.moveinsync.driver.lite": "MoveInSync Partner - Lite (driver)",
    "com.moveinsync.driver.dco": "MoveInSync - Driver Partner (onboarding)",
    "field.moveinsync.ets": "MoveInSync - Field app",
}

# Same-day benchmarks: direct competitors first, then the consumer apps employees compare us to.
COMPETITORS = {
    "in.mtap.iincube.safetrax.commuter": "Safetrax Commuter",
    "com.routematic.employee": "Routematic",
    "com.ubercab": "Uber",
    "com.rapido.passenger": "Rapido",
    "com.olacabs.customer": "Ola",
}

LANG = "en"
COUNTRY = "IN"                       # the listing 99% of users see
OTHER_COUNTRIES = ["US", "PH", "GB", "ZA"]   # same app, different public score

TIMEZONE_OFFSET_MIN = 330            # IST

# Alert thresholds (see pulse/digest.py)
VERSION_MIN_REVIEWS = 30             # a release needs this many written reviews before we judge it
VERSION_ONE_STAR_GAP = 0.08          # release 1-star share minus trailing baseline
THEME_SPIKE_RATIO = 2.0              # last 30 days vs the 180 days before
THEME_SPIKE_MIN = 6
REPLY_SLA_HOURS = 24

# Shown as "Code and data" on the report. Leave empty to hide the link.
REPO_URL = "https://github.com/AlapatiAbhinavChowdhary/playstore-pulse.git"
AUTHOR = "Alapati Abhinav Chowdhary"

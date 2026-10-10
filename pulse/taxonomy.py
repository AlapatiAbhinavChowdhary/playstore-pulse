"""Review theme taxonomy for an employee-commute app.

Each theme has an owner (the team that can actually fix it), a plain-language
label and a set of regular expressions. A review can carry several themes.

The rules are deliberately transparent: a product manager can read this file,
disagree with a line and change it. `python -m pulse validate` reports
precision and recall against the read-and-tagged reviews in data/labels.csv, so a
change to a rule shows up as a number, not an opinion.
"""
import re

# Owner buckets -------------------------------------------------------------
ENG = "App engineering"      # the app is broken
PROD = "Product decisions"   # the app works as designed, and the design is the complaint
OPS = "Ride operations"      # the cab, the route, the driver, the helpdesk
GEN = "No detail given"

_F = re.I | re.S


def _rx(*parts):
    return re.compile("|".join(parts), _F)


# Order matters only for display. (key, label, owner, pattern)
THEMES = [
    # ------------------------------------------------------------------ ENG
    ("install_integrity", "\"Not installed from Play Store\" lock-out, forced reinstall", ENG, _rx(
        r"not\s+(been\s+)?(installed|downloaded|download)\s+(from|through|thru|via|by)\s+(the\s+)?(google\s+)?(play|app)\s*store",
        r"(installed|downloaded)\s+from\s+(the\s+)?(google\s+)?play\s*store",
        r"install\w*\s+(it\s+)?from\s+(the\s+)?play\s*store.{0,60}(error|again|still|only)",
        r"(showing|says?|shows?)\s+(it'?s\s+|as\s+|app\s+)?not\s+installed|app\s+not\s+installed",
        r"un-?install\w*\s+(\w+\s+){0,4}(re-?install\w*|install\w*|download\w*)",
        r"un-?install\w*\s+(\w+\s+){0,3}(to\s+make\s+(this|it)\s+work|every\s?(day|time)|daily|frequent\w*|many\s+times|multiple\s+times)",
        r"(every\s?(day|time)|daily|frequent\w*|again\s+and\s+again|each\s+time)\s+(\w+\s+){0,5}(un-?install|re-?install)",
        r"re-?install\w*\s+(\w+\s+){0,4}(every|again\s+and\s+again|each\s+time|daily|frequent\w*|multiple|many\s+times|\d+\s*times)",
        r"keeps?\s+(on\s+)?(uninstalling|asking\s+to\s+(re-?install|install))",
    )),
    ("launch_crash", "App crashes, freezes or will not open", ENG, _rx(
        r"crash\w*|force\s*clos\w*|keeps?\s+(on\s+)?(stopping|closing)",
        r"clos(es|ed|ing)\s+(itself|automatically|auto|as\s+soon|by\s+itself|in\s+a\s+sec)|(automatic\w*|auto)\s+clos\w*|open\s+and\s+close",
        r"(not|n't|unable\s+to|cannot|never|does\s?nt|doesnt|wont)\s+(even\s+)?(open\w*|launch\w*|start\w*)\b",
        r"not\s+getting\s+open\w*|not\s+open\b|won'?t\s+open|(blank|white|black)\s+(screen|page)|goes\s+blank",
        r"(app|application|screen|it)\s+(\w+\s+){0,2}(hang\w*|freez\w*|frozen|stuck|struck)|\b(hangs?|hanged|hanging|freez\w*|frozen)\b",
        r"stop(ped|s)?\s+working|(app|application|server)\s+(is\s+)?down\b|not\s+compatible|compatib\w+|should\s+be\s+available\s+to",
    )),
    ("app_unstable", "\"Not working\", errors, bugs (no specifics)", ENG, _rx(
        r"not\s+work(ing|s)?\b|never\s+work\w*|doesn'?t\s+(work|function)|does\s+not\s+(work|function)|isn'?t\s+working|non\s?-?functional",
        r"\berrors?\b|something\s+went\s+wrong|\bbugs?\b|\bbuggy\b|glitch\w*|technical\s+(issue|problem|glitch|error)s?|system\s+issue",
        r"stability|unstable|not\s+stable|malfunction\w*|always\s+some\s+(or\s+the\s+other\s+)?issues?|issues?\s+with\s+(the\s+)?(installation|application|app)|full\s+of\s+(issues|problems)",
        r"\bstuck\b|\bstruck\b",
    )),
    ("login_otp", "Login, OTP or being logged out", ENG, _rx(
        r"\botps?\b|one\s*time\s*pass\w*",
        r"(unable|not\s+able|can'?t|cannot|can\s?not|couldn'?t|could\s+not|issue\w*|problem\w*|fail\w*|error|trouble|difficult\w*)\s+(\w+\s+){0,3}(log\s?-?in|sign\s?-?in|logging\s+in|signing\s+in|register\w*)",
        r"(log\s?-?in|sign\s?-?in|logging\s+in|sign\s?up|registration)\s+(\w+\s+){0,2}(issue|problem|fail\w*|error|not\s+work\w*|doesn'?t\s+work|page|screen|is\s+worst)",
        r"logg?(ed|ing|s)\s+(me\s+|us\s+|you\s+)?(out|off)|logs?\s+(me|us|you)\s+out|log\s?-?out\s+(automatically|auto|every|frequent\w*|itself|again|problem|issue|bug|by\s+itself)",
        r"(frequent\w*|auto\w*|keeps?|again|always|sudden\w*|getting)\s+(log\s?-?out\w*|log\s?-?off\w*|sign\w*\s?-?out|logg?ing\s+out)|logouting|logoff|sign(ing|ed|s)\s+out|log\s?-?out\w*\s+is\s+happening",
        r"re-?log\s?in|log\s?-?in\s+(again|every\s?time|each\s+time|repeatedly|daily|every\s?day|always)|(ask\w*|asking|requires?)\s+(us\s+|me\s+|to\s+|for\s+)*(log\s?-?in|sign\s?-?in|re-?login)",
        r"loo?ses\s+my\s+login|save\s+login|session\s+expire\w*|aut?hentication|not\s+verify\w*|verification\s+(code|fail\w*|not)|unable\s+to\s+verify|logged\s+in\s+from\s+the\s+start",
        r"invalid\s+(user|credential|email|mobile|number)|not\s+registered|user\s+not\s+found|password|register\w*\s+(again|option)|registering\s+option",
        r"not\s+(receiv\w+|get\w+|com\w+)\s+(the\s+|any\s+)?(codes?|verification)|codes?\s+(not|never)\s+(receiv\w+|com\w+)",
    )),
    ("performance", "Slow, laggy, network or battery heavy", ENG, _rx(
        r"\bslow\w*\b|sloo+w\w*|\blag\w*\b",
        r"takes?\s+(forever|ages|too\s+long|a\s+lot\s+of\s+time|so\s+much\s+time|too\s+much\s+time|long\s+time|\d+\s*(sec|min)\w*)\s+to\s+(load|open|book|refresh|start|reload)",
        r"load\w*\s+(time|very|too|so|forever|slow\w*|issue)|keeps?\s+(on\s+)?loading|loading\s+(forever|always|only|screen)|time\s+to\s+(load|reload|open)|time\s?-?taking|doesn'?t\s+load|not\s+load\w*",
        r"no\s+network|network\s+(error|issue)|server\s+(error|issue|not)|(app|application|it)\s+(is\s+)?not\s+respond\w*|unresponsive|time\s?out|drain\w*|battery|overheat\w*|heat(s|ing|ed)\b|optimi[sz]ation",
        r"works?\s+only\s+on\s+wifi|mobile\s+data",
    )),
    ("tracking_eta", "Live tracking, cab location or ETA wrong", ENG, _rx(
        r"\btrack\w*|\bgps\b|\beta\b|live\s+location|real\s*-?\s?time|cab\s+location|exact\s+location",
        r"location\s+of\s+(the\s+)?(cab|vehicle|driver|bus|shuttle|van|transport)|(cab|vehicle|driver|bus|shuttle|van)('s)?\s+(current\s+|live\s+|exact\s+)?location",
        r"location\s+(is\s+)?(not|never|wrong|incorrect|inaccurate|stuck|delayed|does|always\s+wrong)|(wrong|incorrect|inaccurate|different|false|fake)\s+(cab\s+)?location",
        r"\bmaps?\b|mapping|arrival\s+time|(wrong|incorrect|inaccurate)\s+(time|timing|eta)\w*|estimated\s+time|\binaccura\w+|accura\w+|zoom\w*",
        r"where\s+(is\s+)?(the\s+|my\s+)?(cab|driver|vehicle|bus)|(cab|vehicle|bus)\s+(has\s+)?arrived|suddenly\s+(it\s+)?shows?\s+up",
    )),
    ("booking_schedule", "Booking, schedule, roster or cancellation blocked", ENG, _rx(
        r"(unable|not\s+able|can'?t|cannot|can\s?not|couldn'?t|fail\w*|issue\w*|problem\w*|error|difficult\w*|not\s+allow\w*|doesn'?t\s+allow|won'?t\s+(let|allow)|does\s+not\s+(let|allow))\s+(\w+\s+){0,4}(book\w*|schedul\w*|roster\w*|cancel\w*|edit|modify|amend\w*|chang\w+\s+(my\s+|the\s+)?(address|shift|location|date))",
        r"(book\w*|schedul\w*|roster\w*|cancel\w*)\s+(\w+\s+){0,3}(not\s+work\w*|fail\w*|issue|problem|error|not\s+(showing|reflect\w*|available|happening|possible|getting)|option\s+(is\s+)?not|disappear\w*|got\s+cancel\w*|gets?\s+cancel\w*|automatically)",
        r"cut\s?-?off|cutoff|\d+\s*(hours?|hrs?)\s+(prior|before|in\s+advance)|hours?\s+prior|adhoc|ad-?hoc|waitlist\w*|wait\s?-?list",
        r"no\s+option\s+(to|for|of)\s+(cancel|book|edit|change|modify)|option\s+to\s+(cancel|edit|modify|schedule|book|change)|(edit|modify|amend\w*)\s+(option|the\s+booking|booking)|edit\s+options?|amendment\w*",
        r"change\s+(my\s+|the\s+)?(address|shift)|chang\w+\s+an?\s+address|address\s+(to\s+get\s+)?updat\w*|auto\w*\s+cancel\w*|cancel\w*\s+by\s+itself|cancel\s+anytime",
        r"trip\s+(is\s+)?not\s+(booked|showing|created|generated)|not\s+showing\s+(my\s+)?(trip|booking|schedule|roster)|bookings?\s+(on\s+\w+\s+)?not\s+showing",
        r"plus\s+button|date\s+range|multiple\s+dates|create\s+any\s+request|trips?\s+are\s+not\s+getting\s+cancel\w*|booking\s+process|makpag\s?book|book\w*\s+(a\s+|the\s+|my\s+)?(cab|ride|trip|shuttle|bus|pickup)\b.{0,40}(not|unable|can'?t|fail|difficult|issue|problem)",
        r"not\s+able\s+to\s+book|unable\s+to\s+book|can'?t\s+book|freezes\s+if\s+too\s+many",
    )),
    ("contact_driver", "Calling or chatting with driver / co-riders fails", ENG, _rx(
        r"(call\w*|contact\w*|chat\w*)\s+(\w+\s+){0,4}(driver|chauffeur|cab\s?mate|cab\s+person|co-?passenger)\w*",
        r"(driver|chauffeur)('s)?\s+(\w+\s+){0,2}(contact|number|mobile|phone)\b|driver\w*\s+(\w+\s+){0,3}call\s+(us|me|is|was|not)",
        r"calling\s+(option|feature|permission|issue|problem)|call\s+(masking|option|feature|button|not\s+connect\w*|doesn'?t\s+connect|is\s+not\s+going)|without\s+balance",
        r"audio\s+is\s+not\s+clear|not\s+able\s+to\s+call|unable\s+to\s+call|can'?t\s+call|chat\s+option|chat\s*\+|\bchat\b|(mobile|phone|contact)\s+(number|no\.?)\s+(is\s+)?(not|never)\s+(visible|show\w*|display\w*|available)",
    )),
    ("boarding_checkin", "Boarding step: QR scan, trip OTP, seat-belt check, check-in", ENG, _rx(
        r"\bqr\b|scann?\w*|check\s?-?in\b|checkin|seat\s?-?\s?(belt|buckle)|boarding\s+(point|activit\w+|otp|pass)",
        r"otp\s+(\w+\s+){0,4}(not\s+(taken|accept\w*|match\w*)|disappear\w*|is\s+wrong|invalid)|(trip|ride|start|end)\s+otp|opt\s+generated",
    )),
    # ----------------------------------------------------------------- PROD
    ("update_regression", "\"The new update / new UI made it worse\"", PROD, _rx(
        r"(new|latest|recent|last|this)\s+(update\w*|version|upgrade\w*|release|enhancement\w*)\b|(new|latest|recent)\s+(ui|ux|design|interface|look|app|changes?|features?)\b",
        r"(after|since|post|before)\s+(the\s+|this\s+|last\s+|latest\s+|recent\s+|new\s+|\d+\w*\s+\w+\s+)?(update\w*|upgrad\w*)|update\s+(is|was|made|has)\b|updates?\s+(are|have)\b|its\s+update",
        r"(old|older|previous|earlier)\s+(version|app|ui|design|interface|one|layout)|bring\s+(it\s+)?back|bring\s+back|roll\s?-?back|revert\b",
        r"used\s+to\s+be|was\s+(much\s+)?(better|good|easy|simple|working\s+fine)\s+(before|earlier|till)|earlier\s+(it\s+)?was|better\s+before|worst\s+update|downgrade\w*|\bui\s+changes",
    )),
    ("ui_ux", "Confusing or hard-to-use interface", PROD, _rx(
        r"\bui\b|\bux\b|user\s?-?\s?friend\w*|confus\w*|complicat\w*|\bcomplex\b|interface|not\s+intuitive|unintuitive",
        r"hard\s+to\s+(use|understand|find|navigate|deal)|difficult\s+to\s+(use|understand|find|navigate|operate)|not\s+(easy|handy)\s+to\s+use|inconvenient",
        r"navigat\w+\s+(inside|in|within|through)\s+the\s+app|(no\s+)?easy\s+navigation|too\s+many\s+(clicks|taps|steps|options)|number\s+of\s+(taps|clicks)|more\s+number\s+of\s+taps",
        r"\bdesign\w*|layout|\bfont\b|dark\s+(mode|theme)|simplif\w*|tutorial|user\s+experience",
    )),
    ("forced_rating", "Forced trip rating / nagging for ratings", PROD, _rx(
        r"(forc\w*|compuls\w*|mandator\w*|keeps?\s+asking|always\s+(keeps\s+)?asking|asking|every\s+(ride|trip|time)|excessively)\s+(\w+\s+){0,6}(rat(e|ing|ings)|play\s?store\s+reviews?|reviews?)\b",
        r"(rat(e|ing|ings)|review\w*)\s+(\w+\s+){0,6}(is\s+forced|forc\w*|compuls\w*|mandator\w*|every\s+(ride|trip|time)|again\s+and\s+again|before\s+the\s+trip|repeatedly)",
        r"(no|without)\s+(\w+\s+){0,3}skip\s+(\w+\s+){0,2}(rating|option)?|skip\s+(the\s+)?(rating|feedback|review)|can'?t\s+skip|option\s+of\s+skip",
        r"requires?\s+you\s+to\s+rate|have\s+to\s+rate|need\s+to\s+rate|if\s+i\s+don'?t\s+rate",
    )),
    ("trip_feedback", "No way to rate / report a trip in the app (or low stars blocked)", PROD, _rx(
        r"(no|not|without|unable|can'?t|cannot|doesn'?t|never|didn'?t)\s+(\w+\s+){0,5}(rat(e|ing)|feedback)\s+(\w+\s+){0,3}(trips?|rides?|drivers?|journey|rout\w*|option|link|section|past|previous|completed|once|after)\b",
        r"(rat(e|ing|ings)|feedback)\s+(option|link|button|section|page|box)\s+(\w+\s+){0,3}(not|missing|removed|disappear\w*|unavailable)",
        r"(no|without)\s+(\w+\s+)?(feedback|rating)\s+(option|link|button|section|provision|mechanism)|(no|without)\s+provision\s+for\s+feedback|doesn'?t\s+allow\s+(\w+\s+)?feedback",
        r"allowed\s+to\s+give\s+[123]\s+star|minimum\s+[45]\s+stars?|only\s+(given\s+)?(options?\s+(like\s+)?)?[45]\s*(or|and|&|,)\s*5|rate\s+(previous|past|old|earlier|completed)\s+trips?",
        r"feedback\s+text\s+box|unable\s+to\s+provide\s+feedback|not\s+able\s+to\s+rate|unable\s+to\s+rate|cannot\s+rate|can'?t\s+rate|trip\s+ratings?\s+(were|was|are|is)\s+not|rating\s+the\s+trip\s+doesn'?t",
        r"don'?t\s+listen\s+to\s+feedback|inflexible\s+to\s+user\s+feedback|(no|not\s+(a\s+)?proper)\s+option\s+to\s+(rate|provide)",
    )),
    ("trip_info", "Trip details hidden: cab number, co-riders, pickup time, history", PROD, _rx(
        r"co-?\s?passenger\w*|cab\s?-?mates?|cab\s+members?|co-?\s?travell?er\w*|co-?\s?rider\w*|fellow\s+(passenger|traveller|rider|employee|cab)\w*|who\s+all|passenger\s+list",
        r"other\s+(passenger|employee|user|member)s?('s)?\s+(location|pick|detail|live)|live\s+location\s+of\s+other",
        r"(cab|car|vehicle|driver)\s+(number|no\.?|details?|info\w*)\s+(\w+\s+){0,3}(not|never|missing|hidden|late|\d+\s+min)|provides?\s+cab\s+number",
        r"(not|n't|never|no)\s+(\w+\s+){0,3}(show\w*|display\w*|see|visible|provid\w*|shar\w*|get\w*|giv\w*)\s+(\w+\s+){0,3}(cab|car|vehicle|driver|trip)s?\s+(number|no\b|details?|info\w*|history)",
        r"trip\s+history|upcoming\s+trips?|(old|previous|past)\s+trips?|view\s+(my\s+)?(all\s+)?bookings?|bookings?\s+later\s+than|exact\s+time\s+of|showing\s+no\s+address|don'?t\s+show\s+any\s+details",
        r"where\s+is\s+the\s+pick|not\s+(showing|displaying)\s+(the\s+)?(pick|drop|route|timing|time)|don'?t\s+display\s+the|no\s+(confirmation|visibility)|details?\s+of\s+previous|monthly\s+view",
        r"received\s+the\s+cab\s+details\s+\d+|sequence\s+(number|and\s+cab)|'?na'?\s+for\s+the\s+sequence",
    )),
    ("notifications", "Notification / alert spam, ads, or missing alerts", PROD, _rx(
        r"notif\w*|pop\s?-?ups?|\balerts?\b|\bsms\b|reminder\w*|too\s+many\s+(message|call)s?|\bads?\b|advertis\w*|buzzer",
    )),
    ("permissions_privacy", "Forced permissions, repeated policy pop-up, privacy", PROD, _rx(
        r"permission\w*|microphone|\bmic\b|privacy|location\s+accuracy|precise\s+location|background\s+location|always\s+allow|battery\s+optimi\w*",
        r"turn\s+on\s+(notification|location|gps)|personal\s+(data|info\w*)|screenshot\w*|automatic\s+date\s+and\s+time",
        r"(terms|agreement\w*|aggreement\w*|polic\w+)\s+(\w+\s+){0,6}(every\s?time|again\s+and\s+again|multiple\s+times|each\s+time|on\s+the\s+launch|repeatedly|acceptance)",
        r"(agree|accept)\s+(\w+\s+){0,5}(every\s?time|again|each\s+time|polic\w+)|asks?\s+to\s+agree|i\s+agree|accept\w*\s+(the\s+)?(transport\s+)?polic\w*",
    )),
    ("workplace_modules", "Non-commute modules: parking, desk, meal, metro", PROD, _rx(
        r"parking|desk\s+(book\w*|allocat\w*|number)|book\w*\s+(a\s+|the\s+|any\s+)?(desk|seat\s+in\s+office)|hot\s?desk|seat\s+(number|booking|allocation)",
        r"\bmeals?\b|cafeteria|\bmetro\b|meeting\s+room|workinsync|work\s+in\s+sync",
    )),
    # ------------------------------------------------------------------ OPS
    ("routing_pickup", "Route, clubbing, pickup time or pickup point", OPS, _rx(
        r"\brout(e|es|ing|ed)\b|club\w*|pick\s?-?\s?up\s+(time|timing|point|location|schedule)s?|(early|earlier)\s+(pick|pickup|log)\w*|too\s+early|pick\s?-?ups?\s+(are\s+|is\s+)?(done\s+|scheduled\s+)?(too\s+|very\s+|so\s+)?early",
        r"\d+(\.\d+)?\s*(hrs?|hours?|hr)\s+(to\s+reach|early|earlier|travel|journey|daily\s+in|in\s+(the\s+)?cab|before\s+(our|my|the)\s+shift)|hours?\s+to\s+reach|\d+\s*(hrs?|hours?)\s+for\s+me\s+to\s+reach",
        r"long(er)?\s+(route|distance|way)|travel\s+time|nodal|drop\s+(point|location|time|timing)s?|stops?\b.{0,20}(far|not|add|more)|door\s?-?step|pickup\s+sequence|detour|opposite\s+(direction|side)",
        r"shortest|pilgrimage|whole\s+city|middle\s+of\s+nowhere|paired\s+with|according\s+to\s+stops|allocates?\s+the\s+trip\s+early|timing\s+allotment|planning\s+(the\s+)?route|plan\w*\s+commutes?",
    )),
    ("cab_late_noshow", "Cab late, not assigned, or unfair no-show", OPS, _rx(
        r"(cab|driver|vehicle|bus|shuttle|van|pick\s?up|they|always|came|comes?|coming|arriv\w*|reach\w*|hour|hrs?|min\w*|sched)\w*\s+(\w+\s+){0,3}late\b|\blate\s+(by|for|every|daily|always|pick\w*|arriv\w*|coming|cab|and)",
        r"later\s+the\s+cab|delay\w*\b(?!\s+notification)|(not|never|don'?t|doesn'?t)\s+(\w+\s+){0,3}on\s?-?time|(come|came|arriv\w*|reach\w*|assign\w*)\s+(\w+\s+){0,2}on\s?-?time|punctual\w*",
        r"wait(ed|ing)?\s+(for\s+)?(\w+\s+){0,3}(\d+\s*(min|hour|hr)|an\s+hour|hours)|\d+\s*(mins?|minutes|hours?|hrs?)\s+(late|delay\w*|wait\w*)|more\s+than\s+an\s+hour",
        r"no\s?-?\s?show",
        r"(cab|vehicle|driver|car|bus|shuttle)s?\s+(\w+\s+){0,3}(not|never|didn'?t|did\s+not|doesn'?t|won'?t|are\s+not|is\s+not|were\s+not)\s+(\w+\s+){0,2}(come|came|arriv\w*|show\w*|turn\w*|assign\w*|allot\w*|allocat\w*|provid\w*|pick\w*|wait\w*|reach\w*)",
        r"(not|never|no)\s+(\w+\s+){0,2}(assign\w*|allot\w*|allocat\w*)\s+(\w+\s+){0,2}(cabs?|vehicle|car)|no\s+cabs?\b|cabs?\s+(is\s+|are\s+|was\s+)?not\s+available|cab\s+not\s+assigned",
        r"miss(ed|ing)?\s+(my\s+|the\s+)?(cabs?|bus|shuttle|flight|shift)|left\s+(without|before)|stranded|time\s+commitment|start\w*\s+before\s+the\s+time|can'?t\s+even\s+wait",
    )),
    ("driver_vehicle", "Driver behaviour, vehicle condition, safety", OPS, _rx(
        r"\brude\w*|misbehav\w*|behaviou?r\w*|\brash\b|over\s?-?speed\w*|speeding|drunk|abus\w+|unprofessional\w*|professonalism|no\s+manners|manners|disrespect\w*|arrogan\w*|careless",
        r"drivers?\s+(\w+\s+){0,3}(bad|worst|rude|useless|pathetic|ridiculous|don'?t\s+know|doesn'?t\s+know|not\s+good|cause|force|tap)|(bad|worst|rude|abusive)\s+drivers?",
        r"\bac\b|air\s?-?con\w*|dirty|unclean|hygien\w*|smell\w*|uncomfortable|unsafe|\bsafety\b|not\s+safe|harass\w*|women|female|girl\w*|escort|marshal|4\s+seater",
    )),
    ("support_channel", "Helpdesk unreachable / complaints go nowhere", OPS, _rx(
        r"help\s?-?\s?desk|help\s?-?line|customer\s+(care|support|service)|support\s+(team|staff|number|system|executive|person|available)|(no|zero|poor|bad|worst|pathetic|rude)\s+(customer\s+)?support",
        r"support\s+(is|was|are)\s+(bad|poor|worst|pathetic|not|zero|rude|unhelpful|very)|(no|zero)\s+(proper\s+)?(response|reply|action|resolution|revert|accountability)",
        r"no\s?(one|body)\s+(\w+\s+){0,2}(respon\w*|repl\w*|answer\w*|pick\w*|listen\w*|help\w*|call\w*|bother\w*|care\w*)|none\s+of\s+them\s+(respon|help)\w*",
        r"(don'?t|doesn'?t|do\s+not|did\s?n'?t|never|not|stopped)\s+(\w+\s+){0,3}(respond\w*|reply\w*|replied|answer\w*|pick\s+(up\s+)?(the\s+)?(call|phone)s?|receiv\w+\s+the\s+call|listen\w*|resolv\w*|consider\w*)",
        r"not\s+reachable|unreachable|(no|without)\s+(any\s+)?(complaint|support|contact|grievance|escalation)\s+(option|link|channel|button|mechanism|system|section|number)",
        r"complain\w*|escalat\w*|raised?\s+(a\s+|the\s+|an\s+|my\s+|many\s+|multiple\s+|it\s+)?(ticket|concern|issue|request|query)\w*|raising\s+(it|a|my)|ticket\w*|deaf\s+ears|ignor\w+|\bsos\b",
        r"transport\s+(team|desk|department|admin\w*|help\w*)|not\s+ready\s+to\s+help|line\s+disconnect\w*|disconnect\w*\s+(in\s+between|the\s+call)|reported\s+the\s+issue|against\s+my\s+report|sent\s+(multiple|many|several)\s+emails|not\s+solved\s+by|no\s+feedback\b",
        r"not\s+(at\s+all\s+)?helping|won'?t\s+help|n'?t\s+help\b|not\s+helpful\s+on|no\s+one\s+is\s+helping",
    )),
    ("service_vendor", "Service / vendor / employer transport policy in general", OPS, _rx(
        r"\bservices?\b|vendors?\b|management|transport(ation)?\s+(provider|facility|company|system|is|was)|facilit\w*|made\s+mandatory|cab\s+provider|\badmin\b|company\s+policy|organi[sz]ations?\b|monopoly",
    )),
]

GENERIC = re.compile(
    r"^\W*((the|this|a|an|very|so|too|such|most|really|totally|absolutely|utter\w*|completely|one|of|its?|it'?s|is|was|just|ever|i|have|had|seen|used|app|aap|apk|apl|application|experience|software|in|my|life|till|now|all|time|to|use|for|not|no|at|world)\s+)*"
    r"(wors[te]\w*|wrost|bad|bekar|bekaar|bakwa+s\w*|useless|pathetic|poor|horribl\w*|terribl\w*|waste\w*|rubbish\w*|disgust\w*|third\s+class|3rd\s+class|not\s+good|not\s+great|disappoint\w*|ridiculous|shit\w*|crap\w*|garbage|trash|faltu|g?hatiya|worthless|awful|hate\w*|nonsense|ok|okay|average|nil|na|no\s+comments?|nothing|good|nice|fine|super|best|great|excellent|unreliable|dislike)"
    r"(\s+(app|aap|apk|apl|application|experience|software|ever|in|my|life|i|have|had|seen|used|till|now|of|all|time|to|use|one|at|and|very|so))*\W*$", _F)

VERDICT = re.compile(
    r"wors[te]\w*|wrost|\bbad\b|bekar|bekaar|bakwa+s\w*|useless|pathetic|\bpoor\w*|horribl\w*|terribl\w*|waste\w*|wastage|rubbish\w*|disgust\w*|(third|3rd)\s+class|not\s+(a\s+|that\s+)?(good|great|useful|helpful|reliable|happy|cool)"
    r"|disappoint\w*|ridiculous|shit\w*|crap\w*|garbage|trash|faltu|g?hatiya|worthless|awful|hate\w*|nonsense|unreliable|improv\w*|never\s+worked|naive|downgrade|sucks?\b"
    r"|not\s+(as\s+)?(useful|recommend\w*|satisf\w*|worth\w*)|recommend\w*\s+not|zero\s+(star|rating)|0\s+star|negative\s+(star|rating)|one\s+star|1\s+star|\bstars?\b|inefficient|dislike|irritat\w*|annoy\w*|frustrat\w*|headache|hassle|stupid|rating",
    _F)

LABEL = {k: label for k, label, owner, rx in THEMES}
OWNER = {k: owner for k, label, owner, rx in THEMES}
LABEL["generic"] = "Generic verdict, no detail (\"worst app\")"
OWNER["generic"] = GEN
LABEL["other"] = "Other / unclassified"
OWNER["other"] = GEN
LABEL["positive_text"] = "Praise written under a low star (mis-tap or sarcasm)"
OWNER["positive_text"] = GEN
ORDER = [k for k, *_ in THEMES] + ["generic", "positive_text", "other"]

_SPECIFIC_ENG = {"install_integrity", "launch_crash", "login_otp", "performance", "tracking_eta",
                 "booking_schedule", "contact_driver", "boarding_checkin"}
_SPECIFIC_OPS = {"routing_pickup", "cab_late_noshow", "driver_vehicle", "support_channel"}


def classify(text: str):
    """Return the list of theme keys for one review text (multi-label)."""
    t = (text or "").strip()
    if not t:
        return ["generic"]
    hits = [k for k, _, _, rx in THEMES if rx.search(t)]
    # the vague buckets only survive when nothing more specific explains the review
    if "app_unstable" in hits and any(h in _SPECIFIC_ENG for h in hits):
        hits.remove("app_unstable")
    if "service_vendor" in hits and any(h in _SPECIFIC_OPS for h in hits):
        hits.remove("service_vendor")
    # the integrity lock-out is the specific cause; don't also count it as a crash
    if "install_integrity" in hits and "launch_crash" in hits:
        hits.remove("launch_crash")
    if hits:
        return hits
    if GENERIC.search(t) or len(t.split()) <= 3:
        return ["generic"]
    if len(t) <= 90 and VERDICT.search(t):
        return ["generic"]
    return ["other"]

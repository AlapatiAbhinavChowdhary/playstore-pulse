"""Build the one-page report (docs/index.html) from the metrics document."""
import json
import os

from . import config

TEMPLATE = os.path.join(os.path.dirname(__file__), "template.html")
SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
</head>
<body>
{body}
</body>
</html>
"""


def body(metrics):
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    payload = json.dumps(metrics, ensure_ascii=False).replace("</", "<\\/")
    return html.replace("/*__METRICS__*/null", payload).replace("__REPO_URL__", getattr(config, "REPO_URL", "") or "").replace("__AUTHOR__", getattr(config, "AUTHOR", "") or "the author")


def build(metrics, path, fragment_path=None):
    """Write a standalone page. `fragment_path` also writes the body-only version (for hosts that add their own shell)."""
    b = body(metrics)
    with open(path, "w", encoding="utf-8") as f:
        f.write(SHELL.format(body=b))
    if fragment_path:
        with open(fragment_path, "w", encoding="utf-8") as f:
            f.write(b)


WINDOW = {"last_90d": "the last 90 days", "last_12m": "the last 12 months", "labelled": "since January 2025", "last_30d": "the last 30 days"}


def markdown(m):
    """RECOMMENDATION.md: the same plan and evidence as the page, for people who read in a diff."""
    L, P, O, R = m["listing"], m["layers"]["peer_level"], m["owners"]["last_12m"], m["replies"]["last_12m"]
    pct = lambda x, d=0: "n/a" if x is None else f"{x * 100:.{d}f}%"
    out = [f"# How are our Play Store ratings? - {m['app_name']}", "",
           f"_Reviews to {m['as_of']}. Generated {m['generated']} by `python -m pulse report`. Do not edit by hand._", "",
           f"**{L['score']:.2f} on {L['ratings']:,} ratings. It should be about {P['score_at_peer_level']:.2f}.**", "",
           f"The gap to the best commute apps is one-star ratings: {pct(L['one_share'], 1)} of MoveInSync's against about {pct(P['peer_one_share'], 1)} "
           f"for Uber, Rapido and Safetrax. Every one of the {m['low_star']['labelled']['n']:,} low-star reviews written since January 2025 was read and tagged. "
           f"Of those that give a reason, {pct(O['app_side'])} are about the app itself, not the cab. "
           f"In the last 12 months {R['low_star_unanswered']:,} of {R['low_star']:,} low-star reviews got no reply.", "",
           "## What to do, in order", ""]
    phase = None
    for a in m["plan"]:
        if a["phase"] != phase:
            phase = a["phase"]
            out += [f"### {phase}", ""]
        e = a["evidence"]
        ev = (f"{e['n']:,} of {e['of']:,} low-star reviews ({pct(e['share'])}), {WINDOW[e['window']]}" if e["n"] is not None
              else f"{R['low_star_unanswered']:,} of {R['low_star']:,} low-star reviews unanswered, the last 12 months" if a["id"] == "A2" else "see the other listings table")
        out += [f"#### {a['id']}. {a['title']}", "", f"- **Owner:** {a['owner']}", f"- **Evidence:** {ev}", "", a["why"], "", "**Exactly what to change**", ""]
        out += [f"{i}. {d}" for i, d in enumerate(a["do"], 1)]
        out += ["", f"**Tomorrow morning:** {a['tomorrow']}", "", f"**Done when:** {a['done_when']}", ""]
    if m.get("impact"):
        out += ["## What the plan should be worth", "", "| Scenario | Low-star reviews avoided per year | One-star share of ratings | Public score |", "|---|---|---|---|",
                f"| Today | 0 of {m['impact'][0]['of']:,} | {pct(L['one_share'], 1)} | {L['score']:.2f} |"]
        out += [f"| {s['scenario']} | {s['low_star_avoided_per_year']:,} | {pct(s['one_star_share'], 1)} | {s['score']:.2f} |" for s in m["impact"]]
        out += ["", "An estimate built on stated assumptions (see `pulse/plan.py`), not a forecast. Replies come on top: Google reports an average lift of 0.7 stars on a negative review that gets one.", ""]
    out += ["## Why people rate 1 to 3 stars", "", f"Low-star reviews, last 12 months (n = {m['low_star']['last_12m']['n']:,}). A review can carry more than one reason.", "",
            "| Reason | Reviews | Share | Owner |", "|---|---|---|---|"]
    out += [f"| {t['label']} | {t['last_12m']['n']:,} | {pct(t['last_12m']['share'])} | {t['owner']} |" for t in m["themes"] if t["last_12m"]["n"] and t["key"] not in ("other", "positive_text")]
    out += ["", "The live page (`docs/index.html`) has the charts, the release table, the reply history and the method."]
    return "\n".join(out) + "\n"

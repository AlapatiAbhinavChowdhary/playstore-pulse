"""The weekly answer to "How are our Play Store ratings?" in one screen of text.

Alerts are deliberately few. Each one names what moved, by how much, and who should look.
"""
import json
import os
import urllib.request

from . import config


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.0f}%"


def alerts(m):
    out = []
    v = m["versions"]
    judged = [r for r in v["rows"] if r["n"] >= config.VERSION_MIN_REVIEWS]
    if judged:
        latest = judged[-1]
        gap = latest["one_share"] - v["baseline_one_share_180d"]
        if gap >= config.VERSION_ONE_STAR_GAP:
            out.append({"level": "critical", "owner": "Release manager",
                        "text": f"Release {latest['version']}: {_pct(latest['one_share'])} of its written reviews are 1-star, "
                                f"against a 180-day baseline of {_pct(v['baseline_one_share_180d'])} ({latest['n']} reviews)."})
        elif gap >= config.VERSION_ONE_STAR_GAP / 2:
            out.append({"level": "watch", "owner": "Release manager",
                        "text": f"Release {latest['version']} is running {gap * 100:.0f} points above the 1-star baseline "
                                f"({_pct(latest['one_share'])} vs {_pct(v['baseline_one_share_180d'])}, {latest['n']} reviews)."})
    n30, n12 = m["low_star"]["last_30d"]["n"], m["low_star"]["last_12m"]["n"]
    for t in m["themes"]:
        if t["key"] in ("generic", "other", "positive_text"):
            continue
        a, b = t["last_30d"]["n"], t["last_12m"]["n"]
        base_rate = (b - a) / max(n12 - n30, 1)          # share in the 11 months before
        expected = base_rate * n30
        if a >= config.THEME_SPIKE_MIN and a >= config.THEME_SPIKE_RATIO * max(expected, 0.5):
            out.append({"level": "critical", "owner": t["owner"],
                        "text": f"{t['label']}: {a} low-star reviews in the last 30 days, about {expected:.0f} expected from the year before."})
    r = m["replies"]
    if r["unanswered_7d"]:
        out.append({"level": "action", "owner": "Support lead",
                    "text": f"{r['unanswered_7d']} low-star reviews from the last 7 days have no reply (target: all answered within {config.REPLY_SLA_HOURS} hours)."})
    f = m.get("flow")
    if f and f.get("valid") and f["new_ratings"] >= 50 and f["one_share"] > (m["listing"]["one_share"] or 0) * 1.5:
        out.append({"level": "critical", "owner": "Product manager",
                    "text": f"New ratings since {f['from']}: {_pct(f['one_share'])} are 1-star ({f['new_ratings']} ratings), well above the listing's {_pct(m['listing']['one_share'])}."})
    return out


def render(m):
    L, w = m["listing"], m["windows"]
    lines = [f"# Play Store pulse - {m['app_name']} - as of {m['as_of']}", ""]
    if L:
        lines.append(f"**Public score {L['score']:.2f}** on {L['ratings']:,} ratings. 1-star share {L['one_share'] * 100:.1f}%.")
    f = m.get("flow")
    if f and f.get("valid"):
        lines.append(f"New ratings {f['from']} to {f['to']}: {f['new_ratings']:,}, averaging {f['mean']:.2f}, {_pct(f['one_share'])} 1-star.")
    else:
        lines.append("New-rating flow: needs two listing snapshots; it appears after the next run.")
    lines += ["", "| Written reviews | n | average | 1-star |", "|---|---|---|---|"]
    for k, name in (("last_30d", "Last 30 days"), ("last_90d", "Last 90 days"), ("last_12m", "Last 12 months"), ("prev_12m", "12 months before")):
        mean = "n/a" if w[k]["mean"] is None else f"{w[k]['mean']:.2f}"
        lines.append(f"| {name} | {w[k]['n']:,} | {mean} | {_pct(w[k]['one_share'])} |")
    al = alerts(m)
    lines += ["", "## Needs attention" if al else "## Nothing needs attention this week", ""]
    for a in al:
        lines.append(f"- **{a['level'].upper()}** ({a['owner']}): {a['text']}")
    lines += ["", f"## Why people rated 1 to 3 stars in the last 30 days ({m['low_star']['last_30d']['n']} reviews)", "",
              "| Reason | Last 30 days | Share | Last 12 months share | Owner |", "|---|---|---|---|---|"]
    for t in sorted(m["themes"], key=lambda t: -t["last_30d"]["n"])[:10]:
        lines.append(f"| {t['label']} | {t['last_30d']['n']} | {_pct(t['last_30d']['share'])} | {_pct(t['last_12m']['share'])} | {t['owner']} |")
    r = m["replies"]["last_12m"]
    lines += ["", f"Replies: {r['low_star'] - r['low_star_unanswered']} of {r['low_star']} low-star reviews answered in the last 12 months. Last reply sent {m['replies']['last_reply']}.",
              "", f"_Themes: {m['classifier']}; {m['read_and_tagged']:,} reviews read and tagged individually. Generated {m['generated']}._"]
    return "\n".join(lines) + "\n"


def post_to_slack(text):
    """Optional: set SLACK_WEBHOOK_URL to have the digest posted. Does nothing otherwise."""
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return False
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()
    return True

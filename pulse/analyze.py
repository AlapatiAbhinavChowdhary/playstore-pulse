"""Turn reviews + listing snapshots into one metrics document (docs/metrics.json).

Everything the report and the weekly digest say comes from this file, so every
number on the page can be traced to a function here.
"""
import datetime as dt
import re

import pandas as pd

from . import classify, config, plan
from . import taxonomy as T

LOW = 3            # "low-star" = 1 to 3 stars
RX = {k: rx for k, _, _, rx in T.THEMES}
GROUPS = {         # how the themes roll up into the stories told in the report
    "Can't get in or stay in": ["login_otp", "install_integrity", "launch_crash", "app_unstable"],
    "Can't find or reach my cab": ["tracking_eta", "contact_driver", "trip_info", "boarding_checkin"],
    "Booking and schedule": ["booking_schedule"],
    "Redesign and usability": ["update_regression", "ui_ux"],
    "Forced asks": ["forced_rating", "trip_feedback", "permissions_privacy", "notifications"],
    "Slow or heavy": ["performance"],
    "The ride itself": ["routing_pickup", "cab_late_noshow", "driver_vehicle", "support_channel", "service_vendor"],
}
DEVICE = re.compile(
    r"\b(one\s?plus\s*\d+\w*|pixel\s*\d+\w*|samsung(\s+(galaxy\s+)?[a-z]\d+\w*)?|galaxy\s*\w+|s2\d\+?|vivo\s*\w+(\s+pro)?|oppo\s*\w+|realme\s*\w+|"
    r"redmi\s*\w+|xiaomi|poco\s*\w+|iqoo\s*\w+|moto\w*\s*\w+|nothing\s+phone|huawei|android\s*(version\s*)?\d+)", re.I)


def _r(x, n=3):
    return None if x is None or pd.isna(x) else round(float(x), n)


def _frame(reviews):
    df = pd.DataFrame(reviews)
    df["stars"] = df["stars"].astype(int)
    df["thumbs_up"] = pd.to_numeric(df["thumbs_up"], errors="coerce").fillna(0).astype(int)
    df["at"] = pd.to_datetime(df["reviewed_at_ist"])
    df["rep_at"] = pd.to_datetime(df["replied_at_ist"].replace("", pd.NaT))
    has_reply = df["reply_text"].fillna("") != ""
    # A reply dated before the review answers an earlier version of it: the user has edited since. It does not count.
    df["stale_reply"] = has_reply & (df["rep_at"] < df["at"])
    df["replied"] = has_reply & ~df["stale_reply"]
    df["app_version"] = df["app_version"].fillna("")
    return df


def _vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)) if v else (0,)


def _stats(d):
    n = len(d)
    return {"n": int(n), "mean": _r(d.stars.mean()) if n else None,
            "one_share": _r((d.stars == 1).mean()) if n else None,
            "low_share": _r((d.stars <= LOW).mean()) if n else None,
            "five_share": _r((d.stars == 5).mean()) if n else None}


def _excerpt(text, rx=None, limit=15):
    """A short verbatim excerpt (at most `limit` words), centred on the words that matched the theme."""
    words = text.strip().split()
    if len(words) <= limit:
        return " ".join(words)
    start = 0
    m = rx.search(text) if rx is not None else None
    if m:
        before = len(text[:m.start()].split())
        start = max(0, min(before - 4, len(words) - limit))
    cut = words[start:start + limit]
    return ("... " if start else "") + " ".join(cut) + (" ..." if start + limit < len(words) else "")


def _snapshot_view(snaps, app_id):
    rows = [s for s in snaps if s["app_id"] == app_id and s["country"] == config.COUNTRY and s.get("score") not in ("", None)]
    if not rows:
        return None
    s = rows[-1]
    h = [int(float(s[f"h{i}"])) for i in range(1, 6)] if s.get("h1") not in ("", None) else None
    out = {"date": s["date"], "app_id": app_id, "title": s.get("title"), "score": _r(s["score"], 4),
           "ratings": int(float(s["ratings"])), "reviews": int(float(s["reviews"])) if s.get("reviews") else None,
           "histogram": h, "installs": int(float(s["installs"])) if s.get("installs") else None, "version": s.get("version") or None}
    if h:
        out["one_share"] = _r(h[0] / sum(h), 4)
        out["five_share"] = _r(h[4] / sum(h), 4)
    return out


def _flow(snaps, app_id):
    """Ratings that arrived between the two most recent snapshots: the only direct view of new-rating quality."""
    rows = [s for s in snaps if s["app_id"] == app_id and s["country"] == config.COUNTRY and s.get("h1") not in ("", None)]
    if len(rows) < 2:
        return None
    a, b = rows[-2], rows[-1]
    d = [int(float(b[f"h{i}"])) - int(float(a[f"h{i}"])) for i in range(1, 6)]
    n = sum(d)
    if n <= 0 or min(d) < 0:      # Google recalculates now and then; skip a window that went backwards
        return {"from": a["date"], "to": b["date"], "valid": False}
    return {"from": a["date"], "to": b["date"], "valid": True, "new_ratings": n, "delta": d,
            "mean": _r(sum((i + 1) * x for i, x in enumerate(d)) / n), "one_share": _r(d[0] / n)}


def analyze(reviews, label_rows, snaps, today=None, app_id=None, validate=True):
    app_id = app_id or config.PRIMARY
    allr = _frame(reviews)
    df = allr[allr.app_id == app_id].copy()
    today = pd.Timestamp(today) if today else df["at"].max().normalize()
    end = today + pd.Timedelta(days=1)
    d365, d90, d30, d180 = (end - pd.Timedelta(days=n) for n in (365, 90, 30, 180))
    labels = classify.load_labels(label_rows)

    # ---- themes: the reference tag where the review was read individually, classifier elsewhere
    scope = df[df["at"] >= "2022-01-01"]
    recs = scope[["review_id", "text"]].to_dict("records")
    clf = classify.build(df[["review_id", "text"]].to_dict("records"), labels)
    themes = classify.themes_for(recs, labels, clf)
    df["themes"] = df.review_id.map(themes)
    df["ref"] = df.review_id.isin(labels.keys())

    m = {"generated": dt.datetime.now(dt.timezone(dt.timedelta(minutes=config.TIMEZONE_OFFSET_MIN))).strftime("%Y-%m-%d %H:%M IST"),
         "as_of": str(today.date()), "app_id": app_id, "app_name": config.APPS.get(app_id, app_id),
         "classifier": clf.name, "read_and_tagged": int(df.ref.sum()),
         "corpus": {"reviews": int(len(df)), "first": str(df["at"].min().date()), "last": str(df["at"].max().date()),
                    "all_apps": int(len(allr))}}

    # ---- 1. the public number
    snap = _snapshot_view(snaps, app_id)
    m["listing"] = snap
    m["flow"] = _flow(snaps, app_id)
    bench = []
    for cid, name in list(config.APPS.items()) + list(config.COMPETITORS.items()):
        s = _snapshot_view(snaps, cid)
        if s and s.get("histogram"):
            bench.append({"app_id": cid, "name": name, "ours": cid in config.APPS, "score": s["score"], "ratings": s["ratings"],
                          "one_share": s["one_share"], "histogram": s["histogram"]})
    m["benchmark"] = bench
    m["countries"] = [{"country": s["country"], "score": _r(s["score"], 2), "reviews": int(float(s["reviews"])) if s.get("reviews") else None}
                      for s in snaps if s["app_id"] == app_id and s["date"] == (snap or {}).get("date") and s.get("score") not in ("", None)]

    # ---- 2. two layers: people who wrote, people who only tapped a star
    written = df.stars.value_counts().reindex(range(1, 6), fill_value=0)
    lay = {"written": {"n": int(len(df)), "mean": _r(df.stars.mean()), "by_star": [int(x) for x in written]}}
    if snap and snap.get("histogram"):
        h = snap["histogram"]
        silent = [max(h[i] - int(written.iloc[i]), 0) for i in range(5)]
        lay["silent"] = {"n": int(sum(silent)), "mean": _r(sum((i + 1) * x for i, x in enumerate(silent)) / sum(silent))}
        lay["text_rate_by_star"] = [_r(min(int(written.iloc[i]) / h[i], 1.0)) if h[i] else None for i in range(5)]
        # what the score would be if our 1-star share matched the best peers
        peers = [b["one_share"] for b in bench if not b["ours"] and b["one_share"] is not None]
        if peers:
            target = sorted(peers)[len(peers) // 2] if len(peers) < 3 else sum(sorted(peers)[:3]) / 3
            n, s = sum(h), sum((i + 1) * x for i, x in enumerate(h))
            remove = (h[0] - target * n) / (1 - target)
            lay["peer_level"] = {"peer_one_share": _r(target, 4), "one_star_to_remove": int(round(remove)),
                                 "score_at_peer_level": _r((s - remove) / (n - remove), 3)}
    last12 = df[df["at"] >= d365]
    lay["median_chars_by_star_12m"] = [int(last12[last12.stars == s].text.str.len().median()) if (last12.stars == s).any() else None for s in range(1, 6)]
    lay["five_star_three_words_or_less_12m"] = _r((last12[last12.stars == 5].text.str.split().str.len() <= 3).mean())
    m["layers"] = lay

    # ---- 3. windows and trend
    prev12 = df[(df["at"] >= d365 - pd.Timedelta(days=365)) & (df["at"] < d365)]
    m["windows"] = {"last_12m": _stats(last12), "prev_12m": _stats(prev12), "last_90d": _stats(df[df["at"] >= d90]),
                    "last_30d": _stats(df[df["at"] >= d30]), "all_time": _stats(df)}
    mon = df[df["at"] >= "2022-01-01"].copy()
    mon["month"] = mon["at"].dt.to_period("M").astype(str)
    g = mon.groupby("month")
    m["monthly"] = [{"month": k, "n": int(len(v)), "mean": _r(v.stars.mean()), "one_share": _r((v.stars == 1).mean()),
                     "low_n": int((v.stars <= LOW).sum()), "reply_rate": _r(v.replied.mean()),
                     "low_reply_rate": _r(v[v.stars <= LOW].replied.mean()) if (v.stars <= LOW).any() else None} for k, v in g]
    yr = df.groupby(df["at"].dt.year)
    m["yearly"] = [{"year": int(k), "n": int(len(v)), "mean": _r(v.stars.mean()), "one_share": _r((v.stars == 1).mean()),
                    "reply_rate": _r(v.replied.mean())} for k, v in yr]

    # ---- 4. releases
    base = df[(df["at"] >= d180)]
    base_one = (base.stars == 1).mean()
    vers = []
    for v, d in last12[last12.app_version != ""].groupby("app_version"):
        if len(d) >= config.VERSION_MIN_REVIEWS:
            first = df[df.app_version == v]["at"].min()
            vers.append({"version": v, "first_seen": str(first.date()), "n": int(len(d)), "mean": _r(d.stars.mean()),
                         "one_share": _r((d.stars == 1).mean()), "flag": bool((d.stars == 1).mean() - base_one >= config.VERSION_ONE_STAR_GAP)})
    vers.sort(key=lambda x: _vkey(x["version"]))
    m["versions"] = {"baseline_one_share_180d": _r(base_one), "rows": vers,
                     "flagged": [v["version"] for v in vers if v["flag"]]}

    # ---- 5. why: themes among low-star reviews
    low = df[(df.stars <= LOW) & df.themes.notna()].copy()
    wins = {"last_12m": low[low["at"] >= d365], "last_90d": low[low["at"] >= d90], "last_30d": low[low["at"] >= d30],
            "prev_12m": low[(low["at"] >= d365 - pd.Timedelta(days=365)) & (low["at"] < d365)],
            "labelled": low[low.ref]}
    m["low_star"] = {k: {"n": int(len(v)), "read_share": _r(v.ref.mean()) if len(v) else None} for k, v in wins.items()}
    m["low_star"]["labelled"]["from"] = str(wins["labelled"]["at"].min().date()) if len(wins["labelled"]) else None
    m["low_star"]["labelled"]["to"] = str(wins["labelled"]["at"].max().date()) if len(wins["labelled"]) else None

    def has(d, k):
        return d.themes.map(lambda t: k in t).astype(bool)

    rows = []
    for k in T.ORDER:
        row = {"key": k, "label": T.LABEL[k], "owner": T.OWNER[k]}
        for w, d in wins.items():
            n = int(has(d, k).sum()) if len(d) else 0
            row[w] = {"n": n, "share": _r(n / len(d)) if len(d) else None}
        pool = wins["last_12m"][has(wins["last_12m"], k)]
        rx = RX.get(k)
        if rx is not None:
            pool = pool[pool.text.map(lambda t: bool(rx.search(t))).astype(bool)]
        pool = pool[pool.text.str.len().between(30, 260)].sort_values(["thumbs_up", "at"], ascending=False)
        row["excerpts"] = [{"text": _excerpt(t, rx), "date": str(a.date()), "stars": int(st)} for t, a, st in zip(pool.text.head(1), pool["at"].head(1), pool.stars.head(1))]
        rows.append(row)
    rows.sort(key=lambda r: -r["last_12m"]["n"])
    m["themes"] = rows

    def owner_split(d):
        if not len(d):
            return None
        own = d.themes.map(lambda t: {T.OWNER[x] for x in t})
        spec = own[own.map(lambda s: s != {T.GEN})]
        return {"n": int(len(d)), "gives_reason": _r(len(spec) / len(d)),
                "app_side": _r(spec.map(lambda s: bool(s & {T.ENG, T.PROD})).mean()),
                "ride_only": _r(spec.map(lambda s: (T.OPS in s) and not (s & {T.ENG, T.PROD})).mean()),
                "engineering": _r(spec.map(lambda s: T.ENG in s).mean()), "product": _r(spec.map(lambda s: T.PROD in s).mean()),
                "operations": _r(spec.map(lambda s: T.OPS in s).mean())}
    m["owners"] = {k: owner_split(v) for k, v in wins.items()}

    grp = []
    for name, keys in GROUPS.items():
        row = {"group": name, "themes": keys}
        for w, d in wins.items():
            n = int(d.themes.map(lambda t: bool(set(t) & set(keys))).sum()) if len(d) else 0
            row[w] = {"n": n, "share": _r(n / len(d)) if len(d) else None}
        grp.append(row)
    m["groups"] = grp

    m["action_counts"] = {w: {"+".join(sorted(a["themes"])): int(d.themes.map(lambda t: bool(set(t) & set(a["themes"]))).sum()) if len(d) else 0
                              for a in plan.ACTIONS if a["themes"]} for w, d in wins.items()}
    if snap and snap.get("histogram"):
        m["impact"] = plan.impact(m, list(zip(wins["last_12m"].stars, wins["last_12m"].themes)))
    m["plan"] = [dict(a, evidence=plan.evidence(a, m)) for a in plan.ACTIONS]

    low["quarter"] = low["at"].dt.to_period("Q").astype(str)
    qs = sorted(q for q in low.quarter.unique() if q >= "2023Q1")
    m["quarterly"] = {"quarters": qs, "n": [int((low.quarter == q).sum()) for q in qs],
                      "read": [bool(low[low.quarter == q].ref.mean() > 0.9) for q in qs],
                      "groups": {name: [_r(low[low.quarter == q].themes.map(lambda t: bool(set(t) & set(keys))).mean()) for q in qs] for name, keys in GROUPS.items()}}
    low["month"] = low["at"].dt.to_period("M").astype(str)
    ms = sorted(x for x in low.month.unique() if x >= "2025-01")
    m["episodes"] = {"months": ms, "low_n": [int((low.month == x).sum()) for x in ms],
                     "series": {k: [int(has(low[low.month == x], k).sum()) for x in ms] for k in ("login_otp", "install_integrity", "launch_crash", "update_regression")}}
    acc = low[(low["at"] >= d180) & low.themes.map(lambda t: bool(set(t) & {"install_integrity", "launch_crash", "app_unstable", "performance"}))]
    dev = {}
    for t in acc.text:
        for hit in DEVICE.findall(t):
            name = re.sub(r"\s+", " ", hit[0]).strip().title()
            dev[name] = dev.get(name, 0) + 1
    m["devices_180d"] = sorted(([k, v] for k, v in dev.items()), key=lambda x: -x[1])[:12]

    # ---- 6. replies
    low12 = last12[last12.stars <= LOW]
    rep = df[df.replied]
    lat = (rep.rep_at - rep["at"]).dt.total_seconds() / 3600
    anyrep = df[df.rep_at.notna()]
    written = anyrep.groupby(anyrep.rep_at.dt.year).size()
    best = max(m["yearly"], key=lambda y: (y["reply_rate"] or 0) if y["n"] > 500 else 0)
    m["replies"] = {"last_12m": {"reviews": int(len(last12)), "replied": int(last12.replied.sum()), "low_star": int(len(low12)),
                                 "low_star_unanswered": int((~low12.replied).sum()), "low_reply_rate": _r(low12.replied.mean()),
                                 "stale": int(last12.stale_reply.sum())},
                    "last_reply": str(anyrep.rep_at.max().date()) if len(anyrep) else None,
                    "written_by_year": {int(k): int(v) for k, v in written.items()},
                    "best_year": {"year": best["year"], "reply_rate": best["reply_rate"],
                                  "median_hours": _r(lat[rep["at"].dt.year == best["year"]].median(), 1)},
                    "unanswered_7d": int(((df["at"] >= end - pd.Timedelta(days=7)) & (df.stars <= LOW) & ~df.replied).sum())}

    # ---- 7. what happy users still ask for (4-5 stars, classifier)
    hi = last12[(last12.stars >= 4) & (last12.text.str.len() > 40) & last12.themes.notna()]
    asks = {}
    for t in hi.themes:
        for k in t:
            if k not in ("generic", "other", "positive_text", "service_vendor"):
                asks[k] = asks.get(k, 0) + 1
    m["happy_but"] = {"n": int(len(hi)), "themes": sorted(([T.LABEL[k], v] for k, v in asks.items()), key=lambda x: -x[1])[:8]}
    since_ts = wins["labelled"]["at"].min().normalize() if len(wins["labelled"]) else d365
    since = df[df["at"] >= since_ts]
    feats = {"Chat or message the driver": r"\bchat\b|messag\w+\s+(the\s+)?driver|message\s+feature|chat\s+option",
             "Dark mode": r"dark\s*(mode|theme)", "See co-riders and pickup order": r"co-?\s?passenger|cab\s?-?mates?|who\s+all|fellow\s+(passenger|cab)",
             "Stop the map zooming out": r"zoom", "Offline trip card": r"offline|\bcache\b", "Rate or report a trip later": r"rate\s+(previous|past)|feedback\s+for\s+past|rate\s+trips?\s+at\s+least"}
    m["feature_asks"] = {"since": str(since_ts.date()), "rows": sorted(([k, int(since.text.map(lambda t, _v=v: bool(re.search(_v, t, re.I))).sum())] for k, v in feats.items()), key=lambda x: -x[1])}

    # ---- 8. the other apps
    others = []
    for aid, name in config.APPS.items():
        if aid == app_id:
            continue
        d = allr[allr.app_id == aid]
        s = _snapshot_view(snaps, aid)
        others.append({"app_id": aid, "name": name, "score": s["score"] if s else None, "ratings": s["ratings"] if s else None,
                       "one_share": s.get("one_share") if s else None, "written": int(len(d)),
                       "written_since_2025": int((d["at"] >= "2025-01-01").sum()) if len(d) else 0})
    m["other_apps"] = others

    if validate and labels:
        try:
            cv = classify.cross_validate(df[["review_id", "text"]].to_dict("records"), labels)
            m["validation"] = {"labelled": cv["hybrid"]["_micro"]["n"], "rules": cv["rules"]["_micro"], "hybrid": cv["hybrid"]["_micro"],
                               "per_theme": {k: v for k, v in cv["hybrid"].items() if not k.startswith("_")}}
        except ImportError:
            m["validation"] = None
    from . import digest
    m["alerts"] = digest.alerts(m)
    return m

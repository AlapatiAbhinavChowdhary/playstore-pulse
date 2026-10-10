"""Command line.

  python -m pulse run        fetch new reviews + listing snapshot, analyse, rebuild the report and digest
  python -m pulse fetch      only fetch
  python -m pulse report     only analyse + rebuild docs/ from the data on disk
  python -m pulse digest     print the weekly digest
  python -m pulse validate   classifier precision / recall against the reference tags
  python -m pulse show THEME [--since YYYY-MM-DD] [--stars 3]   print the reviews behind a theme
  python -m pulse audit [--n 50]   print a random sample of read-and-tagged reviews, to check the tags yourself
"""
import argparse
import json
import os
import sys

from . import analyze, classify, config, digest, playstore, report, store

DATA = "data"
REVIEWS = os.path.join(DATA, "reviews.csv")
LABELS = os.path.join(DATA, "labels.csv")
SNAPS = os.path.join(DATA, "snapshots.csv")
DOCS = "docs"


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def cmd_fetch(args):
    known = {}
    for r in store.read_rows(REVIEWS):
        known.setdefault(r["app_id"], set()).add(r["review_id"])
    for app_id, name in config.APPS.items():
        ids = frozenset() if args.full else frozenset(known.get(app_id, ()))
        log(f"Reviews: {name}")
        got = list(playstore.fetch_reviews(app_id, config.LANG, config.COUNTRY, known_ids=ids, log=log))
        added, updated = store.merge_reviews(REVIEWS, app_id, got, config.LANG)
        log(f"  +{added} new, {updated} changed")
    log("Listings")
    for app_id in list(config.APPS) + list(config.COMPETITORS):
        store.append_snapshot(SNAPS, playstore.fetch_listing(app_id, config.LANG, config.COUNTRY))
    for c in config.OTHER_COUNTRIES:
        store.append_snapshot(SNAPS, playstore.fetch_listing(config.PRIMARY, config.LANG, c))
    log("Fetch complete.")


def _metrics(validate=True):
    reviews = store.read_rows(REVIEWS)
    if not reviews:
        sys.exit("No reviews on disk. Run: python -m pulse fetch")
    # "Today" is the date of the newest review on disk, so the same data always gives the same page.
    return analyze.analyze(reviews, store.read_rows(LABELS), store.read_rows(SNAPS), today=os.environ.get("PULSE_TODAY"), validate=validate)


def cmd_report(args):
    m = _metrics()
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    text = digest.render(m)
    with open(os.path.join(DOCS, "digest.md"), "w", encoding="utf-8") as f:
        f.write(text)
    report.build(m, os.path.join(DOCS, "index.html"))
    with open("RECOMMENDATION.md", "w", encoding="utf-8") as f:
        f.write(report.markdown(m))
    log(f"Wrote {DOCS}/index.html, {DOCS}/metrics.json, {DOCS}/digest.md, RECOMMENDATION.md")
    return text


def cmd_digest(args):
    text = digest.render(_metrics(validate=False))
    print(text)
    if args.post and digest.post_to_slack(text):
        log("Posted to Slack.")


def cmd_show(args):
    """The drill-down: every review tagged with a theme, newest first, with version and stars."""
    from . import taxonomy as T
    if args.theme not in T.LABEL:
        sys.exit("Unknown theme. Choose from: " + ", ".join(T.ORDER))
    reviews = [r for r in store.read_rows(REVIEWS) if r["app_id"] == config.PRIMARY and r["reviewed_at_ist"][:10] >= args.since and int(r["stars"]) <= args.stars]
    labels = classify.load_labels(store.read_rows(LABELS))
    clf = classify.build([r for r in store.read_rows(REVIEWS) if r["app_id"] == config.PRIMARY], labels)
    themes = classify.themes_for(reviews, labels, clf)
    hits = [r for r in reviews if args.theme in themes[r["review_id"]]]
    print(f"{T.LABEL[args.theme]} - owner: {T.OWNER[args.theme]} - {len(hits)} reviews of {len(reviews)} since {args.since} (stars <= {args.stars})\n")
    for r in hits:
        src = "read" if r["review_id"] in labels else "model"
        print(f"{r['reviewed_at_ist'][:10]}  {r['stars']}*  v{r['app_version'] or '?':9s} [{src}]  {r['text']}")


def cmd_audit(args):
    import random
    from . import taxonomy as T
    labels = classify.load_labels(store.read_rows(LABELS))
    pool = [r for r in store.read_rows(REVIEWS) if r["review_id"] in labels]
    random.Random(args.seed).shuffle(pool)
    print(f"{min(args.n, len(pool))} of {len(pool)} read-and-tagged reviews (seed {args.seed}). Disagree with a tag? Edit data/labels.csv and re-run.\n")
    for r in pool[:args.n]:
        print(f"{r['reviewed_at_ist'][:10]}  {r['stars']}*  {r['text']}\n      -> " + "; ".join(T.LABEL[t] for t in labels[r["review_id"]]) + "\n")


def cmd_validate(args):
    reviews = [r for r in store.read_rows(REVIEWS) if r["app_id"] == config.PRIMARY]
    labels = classify.load_labels(store.read_rows(LABELS))
    cv = classify.cross_validate(reviews, labels)
    print(f"{cv['hybrid']['_micro']['n']} read-and-tagged reviews, 5-fold cross-validation\n")
    print(f"{'theme':22s} {'n':>5s}   rules P/R      rules+model P/R")
    for k in sorted(k for k in cv["hybrid"] if not k.startswith("_")):
        a, b = cv["rules"][k], cv["hybrid"][k]
        f = lambda x: "  - " if x is None else f"{x:.2f}"
        print(f"{k:22s} {b['n']:5d}   {f(a['precision'])} / {f(a['recall'])}    {f(b['precision'])} / {f(b['recall'])}")
    for name in ("rules", "hybrid"):
        mi = cv[name]["_micro"]
        print(f"\n{name:7s} micro precision {mi['precision']:.3f}  recall {mi['recall']:.3f}  F1 {mi['f1']:.3f}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pulse", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch"); f.add_argument("--full", action="store_true", help="re-read every review, not only new ones")
    r = sub.add_parser("run"); r.add_argument("--full", action="store_true"); r.add_argument("--post", action="store_true")
    sub.add_parser("report")
    d = sub.add_parser("digest"); d.add_argument("--post", action="store_true", help="also post to SLACK_WEBHOOK_URL")
    sub.add_parser("validate")
    au = sub.add_parser("audit"); au.add_argument("--n", type=int, default=50); au.add_argument("--seed", type=int, default=7)
    sh = sub.add_parser("show"); sh.add_argument("theme"); sh.add_argument("--since", default="2025-01-01"); sh.add_argument("--stars", type=int, default=3)
    args = ap.parse_args(argv)
    if args.cmd == "fetch":
        cmd_fetch(args)
    elif args.cmd == "report":
        cmd_report(args)
    elif args.cmd == "digest":
        cmd_digest(args)
    elif args.cmd == "validate":
        cmd_validate(args)
    elif args.cmd == "show":
        cmd_show(args)
    elif args.cmd == "audit":
        cmd_audit(args)
    elif args.cmd == "run":
        cmd_fetch(args)
        text = cmd_report(args)
        if args.post:
            digest.post_to_slack(text)


if __name__ == "__main__":
    main()

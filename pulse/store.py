"""Flat-file storage. CSVs on purpose: diffable in git, openable in Excel."""
import csv
import datetime as dt
import os

from . import config

REVIEW_COLS = ["app_id", "review_id", "reviewed_at_ist", "stars", "thumbs_up", "app_version",
               "replied_at_ist", "text", "reply_text", "lang"]
SNAP_COLS = ["date", "app_id", "country", "title", "score", "ratings", "reviews",
             "h1", "h2", "h3", "h4", "h5", "installs", "version"]

_TZ = dt.timezone(dt.timedelta(minutes=config.TIMEZONE_OFFSET_MIN))


def ist(epoch):
    return dt.datetime.fromtimestamp(epoch, _TZ).strftime("%Y-%m-%d %H:%M:%S") if epoch else ""


def today_ist():
    return dt.datetime.now(_TZ).strftime("%Y-%m-%d")


def read_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(path, rows, cols):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def merge_reviews(path, app_id, fetched, lang="en"):
    """Upsert fetched reviews (dicts from playstore.fetch_reviews). Returns (added, updated)."""
    rows = read_rows(path)
    index = {(r["app_id"], r["review_id"]): r for r in rows}
    added = updated = 0
    for r in fetched:
        rec = {
            "app_id": app_id, "review_id": r["review_id"], "reviewed_at_ist": ist(r["at_epoch"]),
            "stars": r["stars"], "thumbs_up": r["thumbs_up"], "app_version": r["app_version"],
            "replied_at_ist": ist(r["replied_epoch"]), "text": r["text"], "reply_text": r["reply_text"], "lang": lang,
        }
        key = (app_id, r["review_id"])
        if key in index:
            old = index[key]
            if any(str(old.get(c, "")) != str(rec[c]) for c in ("stars", "text", "reply_text", "thumbs_up")):
                old.update(rec)
                updated += 1
        else:
            index[key] = rec
            rows.append(rec)
            added += 1
    rows.sort(key=lambda x: (x["app_id"], x["reviewed_at_ist"]), reverse=True)
    write_rows(path, rows, REVIEW_COLS)
    return added, updated


def append_snapshot(path, listing, date=None):
    """One row per app/country/day. Re-running the same day overwrites that day's row."""
    date = date or today_ist()
    rows = [r for r in read_rows(path)
            if not (r["date"] == date and r["app_id"] == listing["app_id"] and r["country"] == listing["country"])]
    h = listing.get("histogram") or [None] * 5
    rows.append({
        "date": date, "app_id": listing["app_id"], "country": listing["country"], "title": listing.get("title"),
        "score": listing.get("score"), "ratings": listing.get("ratings"), "reviews": listing.get("reviews"),
        "h1": h[0], "h2": h[1], "h3": h[2], "h4": h[3], "h5": h[4],
        "installs": listing.get("installs"), "version": listing.get("version"),
    })
    rows.sort(key=lambda x: (x["date"], x["app_id"], x["country"]))
    write_rows(path, rows, SNAP_COLS)

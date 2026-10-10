"""Minimal Google Play client: one listing call, one reviews call.

Uses the same public endpoints the Play Store website calls. No login, no API
key. Reviewer names and avatars are dropped at parse time, and first names in
developer-reply greetings are stripped: the pulse keeps what was said, not who said it.

The two parsers are pure functions and are unit-tested against responses
recorded from the live store (tests/fixtures).
"""
import json
import re
import time
import urllib.parse
import urllib.request

BASE = "https://play.google.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
SORT_NEWEST = 2
PAGE_SIZE = 199

_DS = re.compile(r"AF_initDataCallback\(\{key: '(ds:\d+)', hash: '\d+', data:(.*?), sideChannel: \{\}\}\);</script>", re.S)


def _get(obj, path, default=None):
    try:
        for k in path:
            obj = obj[k]
        return obj
    except (IndexError, KeyError, TypeError):
        return default


def _http(url, data=None, timeout=30, retries=3):
    headers = {"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.9"}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # network hiccup or rate limit: back off and retry
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Play Store request failed after {retries} tries: {last}")


# ----------------------------------------------------------------- listing
def parse_listing(html):
    """Pull score, rating histogram, installs and version out of a details page."""
    blocks = {}
    for key, raw in _DS.findall(html):
        try:
            blocks[key] = json.loads(raw)
        except ValueError:
            continue
    # ds:5 today; fall back to any block that carries the rating node
    data = blocks.get("ds:5")
    if _get(data, [1, 2, 51]) is None:
        data = next((b for b in blocks.values() if _get(b, [1, 2, 51]) is not None), data)
    hist = _get(data, [1, 2, 51, 1])
    return {
        "title": _get(data, [1, 2, 0, 0]),
        "score": _get(data, [1, 2, 51, 0, 1]),
        "ratings": _get(data, [1, 2, 51, 2, 1]),
        "reviews": _get(data, [1, 2, 51, 3, 1]),
        "histogram": [_get(hist, [i, 1]) for i in range(1, 6)] if hist else None,
        "installs_label": _get(data, [1, 2, 13, 0]),
        "installs": _get(data, [1, 2, 13, 2]),
        "version": _get(data, [1, 2, 140, 0, 0, 0]),
        "updated_epoch": _get(data, [1, 2, 145, 0, 1, 0]),
        "released": _get(data, [1, 2, 10, 0]),
        "whats_new": _get(data, [1, 2, 144, 1, 1]),
    }


def fetch_listing(app_id, lang="en", country="IN"):
    q = urllib.parse.urlencode({"id": app_id, "hl": lang, "gl": country})
    out = parse_listing(_http(f"{BASE}/store/apps/details?{q}"))
    out.update(app_id=app_id, country=country)
    return out


# ----------------------------------------------------------------- reviews
def _payload(app_id, count, token):
    page = f'[{count},null,"{token}"]' if token else f"[{count}]"
    inner = f'[null,[2,{SORT_NEWEST},{page},null,[null,null,null,null,null,null,null,null,null]],["{app_id}",7]]'
    freq = json.dumps([[["oCPfdb", inner, None, "generic"]]])
    return urllib.parse.urlencode({"f.req": freq}).encode()


_GREETING = re.compile(r"^\s*(?i:hi|hello|hey|dear)\b[\s,]+(?!Team\b|There\b|User\b|Sir\b|Madam\b|All\b)[A-Z][\w.'-]*(\s+[A-Z][\w.'-]*)?\s*[,!:]+\s*")


_SIGNOFF = re.compile(r",\s+[A-Z][\w.'-]*\s*([!.]+)\s*$")


def scrub_reply(text):
    """Developer replies often open with the reviewer's first name. Drop it: we keep what was said, not who it was said to."""
    if not text:
        return ""
    return _SIGNOFF.sub(r"\1", _GREETING.sub("Hi, ", text, count=1))


def parse_reviews_response(text):
    """Return (rows, next_token) from one batchexecute response."""
    body = re.sub(r"^\)\]\}'\s*", "", text)
    outer = json.loads(body)
    payload = json.loads(outer[0][2])
    rows = []
    for r in payload[0] or []:
        rows.append({
            "review_id": r[0],
            "stars": r[2],
            "text": " ".join((r[4] or "").split()),
            "at_epoch": _get(r, [5, 0]),
            "thumbs_up": r[6] or 0,
            "app_version": _get(r, [10]) or "",
            "reply_text": scrub_reply(" ".join((_get(r, [7, 1]) or "").split())),
            "replied_epoch": _get(r, [7, 2, 0]) or 0,
        })
    token = _get(payload, [1, 1])
    return rows, token if isinstance(token, str) else None


def fetch_reviews(app_id, lang="en", country="IN", known_ids=frozenset(), max_pages=400, pause=0.4, log=None):
    """Yield reviews newest-first. Stops early once a full page is already known."""
    url = f"{BASE}/_/PlayStoreUi/data/batchexecute?" + urllib.parse.urlencode({"hl": lang, "gl": country})
    token, pages = None, 0
    while pages < max_pages:
        rows, token = parse_reviews_response(_http(url, data=_payload(app_id, PAGE_SIZE, token)))
        pages += 1
        fresh = [r for r in rows if r["review_id"] not in known_ids]
        for r in rows:          # yield everything: an edited review keeps its id but changes text/stars
            yield r
        if log:
            log(f"  {app_id}: page {pages}, {len(rows)} reviews, {len(fresh)} new")
        if not rows or not token or (known_ids and not fresh):
            break
        time.sleep(pause)

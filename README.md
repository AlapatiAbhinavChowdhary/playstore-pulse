# Play Store Pulse

Answers one question for MoveInSync, today and every Monday after: **how are our Play Store ratings, why, and what do we do first?**

A case study by Alapati Abhinav Chowdhary for MoveInSync's Forward Deployed Engineer process. Independent work on public Play Store data; not an official MoveInSync project.

| | |
|---|---|
| **The recommendation, as a page** | `docs/index.html` (served by GitHub Pages) |
| **The recommendation, as text** | [RECOMMENDATION.md](RECOMMENDATION.md) |
| **How I got there and which tools I used** | [METHOD.md](METHOD.md) |
| **This week's digest** | [docs/digest.md](docs/digest.md) |

## The answer in six lines (reviews to 2026-10-09)

1. The employee app is rated **4.64** on 114,835 ratings. Uber, Rapido and Safetrax sit at 4.72 to 4.73.
2. The whole gap is one-star ratings: **6.4%** of MoveInSync's against about 3.8% for those three. At their level the same histogram reads **4.74**.
3. Of the low-star reviews that give a reason, **78%** are about the app and 22% only about the ride.
4. The largest group cannot get in or stay in: login, OTP, logged out, locked out, crash (24% of low-star reviews in the last 12 months). A lock-out bug is live now.
5. Replies stopped in July 2024. In the last 12 months **828 of 849** low-star reviews got no answer.
6. Ten actions in three phases. If all land, the estimate is about 358 fewer low-star reviews a year and a score near **4.74**.

## Run it

```bash
pip install -r requirements.txt

python -m pulse run                 # fetch new reviews + listing snapshot, analyse, rebuild docs/ and RECOMMENDATION.md
python -m pulse digest              # the one-screen weekly answer, with alerts
python -m pulse show login_otp --since 2026-01-01     # the reviews behind any reason, with version and date
python -m pulse validate            # classifier precision / recall against the read-and-tagged reviews
python -m pulse audit --n 50        # a random sample of tagged reviews, to check the tags yourself
python -m unittest discover -s tests
```

The first run reads every review (about three minutes, roughly 125 requests). Later runs stop at the first page with nothing new.
Review text is not committed to this repository; `fetch` rebuilds it from the public store. Reviewer names and photos are not collected.

`.github/workflows/pulse.yml` runs the whole thing every Monday at 09:00 IST, commits the refreshed page and snapshot, and posts the digest to Slack if `SLACK_WEBHOOK_URL` is set.

## How it works

```
Play Store (public)                pulse/playstore.py   listing + reviews, no login, no reviewer identity
        |
data/reviews.csv, snapshots.csv    pulse/store.py       flat files; one listing row per app per day
        |
reason per review                  pulse/taxonomy.py    22 reasons, each with an owning team, as readable rules
                                   pulse/classify.py    rules + a small model trained on data/labels.csv
        |
docs/metrics.json                  pulse/analyze.py     every number on the page comes from here
        |
docs/index.html, digest.md,        pulse/report.py      the page
RECOMMENDATION.md                  pulse/digest.py      the weekly text and its alerts
                                   pulse/plan.py        the ten actions, as data; evidence counts filled in live
```

Three design choices worth knowing:

- **The plan is data.** `pulse/plan.py` names the reasons each action answers. The evidence counts and the impact estimate are recomputed on every run, so the page that makes the recommendation is also the page that shows whether it is working.
- **A tag from reading the review beats a tag from the classifier.** 1,649 low-star reviews (every one since January 2025) were read individually and tagged; those tags are used as they are. The classifier covers everything else and is scored against them: precision 0.76, recall 0.81 in 5-fold cross-validation.
- **Snapshots make the invisible visible.** Play shows a score, not the flow of new ratings behind it. Saving the star histogram on every run lets the pulse report how many 1-star to 5-star ratings arrived in between, which is where a change shows up first.

## Point it at another app

Edit `pulse/config.py`: the app ids, the peers to benchmark against, the countries, the alert thresholds.
For a different product, start from `pulse/taxonomy.py`; the reasons there are specific to an employee-commute app
("login trip" means the ride to the office, not signing in).

## Limits

- Reviews come from a self-selected few. They show what goes wrong, not how often it goes wrong for every rider.
- The impact table is a scenario on stated assumptions (`avoidable` in `pulse/plan.py`), not a forecast.
- The fetcher is tested against responses recorded from the live store and a local replay server. If Google changes the page format, `tests/test_playstore.py` is where it will show.
- Crash rates, login success and in-app ratings live inside MoveInSync. Joining them to these reasons is the obvious next step.

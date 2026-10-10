# How I got there, and which tools I used

## The short version

1. **Looked before assuming.** The brief says the ratings are lower than they should be. The first thing checked was the number itself: 4.64 on 114,835 ratings, which is not obviously low. So the question became "lower than what, and where is the loss?" Benchmarking against five apps on the same day showed the gap is entirely in one-star ratings (6.4% against about 3.8%).
2. **Got all the data, not a sample.** Every written review on the India listing: 24,331 for the employee app from 2014-03-14 to 2026-10-09, plus 126 for the three smaller MoveInSync listings, with star rating, date, app version, helpful votes and any developer reply. Also the public rating histogram for each listing, four other country listings, and five peer apps.
3. **Read the complaints instead of counting keywords.** All 1,649 low-star reviews (1 to 3 stars) written since 1 January 2025 were read one at a time and tagged against a fixed list of 22 reasons, several tags allowed per review. Each reason has an owning team: app engineering, product decisions, or ride operations.
4. **Checked the tagging could be repeated.** A classifier (readable rules plus a small model trained on the tagged set) scores precision 0.76 and recall 0.81 against those tags in 5-fold cross-validation. It handles older reviews, high-star reviews and future runs.
5. **Looked for causes in time.** Reasons by month, one-star share by app release, replies by month. That is how the login incidents, the returning lock-out bug and the end of developer replies in July 2024 showed up.
6. **Turned findings into a plan a team can start on.** Ten actions, each with an owner, the reviews behind it, the exact changes, the first step for tomorrow morning and the number that says it worked.
7. **Made the answer repeatable.** The brief says this question will be asked again. So the deliverable is a program: one command refreshes the data, the page and a weekly digest with alerts, on a schedule.

## Tools

| Tool | What it did |
|---|---|
| **Claude (Anthropic), working as an agent** | Did most of the hands-on work: wrote and ran the collection code, read and tagged the 1,649 low-star reviews in batches of about 165, wrote the analysis pipeline, the tests and the report page, and drafted the recommendation. |
| **Google Play public endpoints** | The same listing page and review feed the Play Store website uses. No login and no API key. Collected through a normal Chrome session on 10 October 2026. |
| **Python** (pandas, scikit-learn) | Storage, analysis, the classifier and its cross-validation. |
| **Plain HTML, CSS and JavaScript** | The report page: no framework, one file, charts drawn from `docs/metrics.json`. |
| **GitHub Actions and Pages** | The weekly run and the hosting. |

## What a reader should not assume

- **The tags were assigned by an AI model reading each review, not by a person.** They are in `data/labels.csv`, and `python -m pulse audit` prints a random sample with the text beside the tags. The right next check is a person re-tagging 100 of them blind and measuring agreement.
- **Reasons are counted among people who chose to write.** 849 low-star reviews in a year, from a product used by more than a million people a day. They tell you what breaks. They do not tell you the rate at which it breaks. Crash and login telemetry would.
- **Play's histogram is weighted toward recent ratings**, so "star-only ratings average about 4.9" is an approximation from subtracting written reviews from the public histogram.
- **The score estimate is a scenario.** Each action is assumed to prevent between 30% and 80% of the reviews that carry its reasons. The assumptions are one field per action in `pulse/plan.py`; change them and the table changes.
- **A reply dated before the review does not count as an answer.** 22 reviews in the last 12 months carry an old reply to an earlier version of the review. Counting those would have made the reply rate look better than it is; a first pass of this analysis had that wrong.
- **The Python fetcher has been tested against recorded responses and a local replay server**, and the same requests were run successfully in a browser. Run `python -m pulse fetch` once on a normal network to confirm it end to end.

## Decisions made, and why

- **India listing, English reviews.** That is the listing nearly all riders see. Reviews in 12 other languages were checked for and total 20.
- **Low-star means 1 to 3.** Three-star reviews read as complaints with a polite rating.
- **Theme analysis starts in January 2025.** Older reviews describe an app that no longer exists; the long history is used only for trends.
- **Review text is not republished.** The repository holds the tags, the aggregates and the code that rebuilds the data. Reviewer names were not collected.
- **No quotes longer than a line.** The page shows one short excerpt. The drill-down command (`pulse show`) is where an engineer reads the users' own words.

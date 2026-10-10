# How are our Play Store ratings? - MoveInSync (employee app)

_Reviews to 2026-10-09. Generated 2026-10-10 13:52 IST by `python -m pulse report`. Do not edit by hand._

**4.64 on 114,835 ratings. It should be about 4.74.**

The gap to the best commute apps is one-star ratings: 6.4% of MoveInSync's against about 3.8% for Uber, Rapido and Safetrax. Every one of the 1,649 low-star reviews written since January 2025 was read and tagged. Of those that give a reason, 78% are about the app itself, not the cab. In the last 12 months 828 of 849 low-star reviews got no reply.

## What to do, in order

### This week

#### A1. Hotfix the "not installed from Play Store" lock-out and the launch crashes

- **Owner:** Android lead
- **Evidence:** 35 of 224 low-star reviews (16%), the last 90 days

A new failure is live right now. From March 2025 to May 2026 this lock-out was almost absent; since versions 12.16 to 12.19 it is back, and together with launch crashes it is the largest current reason for a low rating. People say the app claims it was not installed from Play Store, refuses to open, and only a reinstall brings it back, until it happens again a few days later. Several say it starts two to three days after an install or update, which points at a cached verdict or licence check expiring rather than at the install itself. Reviewers name OnePlus 12, Pixel 8 on Android 17, Vivo V25 Pro and Samsung S22+.

**Exactly what to change**

1. Open Play Console > Android vitals. Pull crash and ANR clusters for 12.16.0 to 12.20.0, split by Android version and device model.
2. Find the installer-source / Play Integrity check behind that error text. Make it fail open: on a failed or inconclusive verdict, retry in the background and let the user in. Log the verdict to the server; never block and never ask for a reinstall.
3. Test the auto-update path (update while logged in, then cold start) on Android 15, 16 and 17.
4. Ship as a staged rollout: 10% > 50% > 100%, halting if crash-free sessions drop under 99.5%.
5. Reply to every reviewer who reported it with the version that fixes it.

**Tomorrow morning:** Run: python -m pulse show install_integrity --since 2026-06-01. That prints the repro list: dates, versions, devices, the user's own words. Then reproduce by updating 12.15 to 12.19 through Play on a Pixel 8.

**Done when:** No new review in this theme for 30 days, and crash-free users at or above 99.5% on the newest Android version.

#### A2. Answer every 1 to 3 star review within 24 hours

- **Owner:** Support lead
- **Evidence:** 828 of 849 low-star reviews unanswered, the last 12 months

The team used to do this and stopped. In 2023 almost every review got a reply, typically within 15 hours. Since July 2024 almost none do. The few replies still going out are short templates. A brief restart in late 2025 answered about eighty reviews and lapsed, which says this needs an owner and a queue, not a campaign. Google's own figure is that replying to a negative review lifts that rating by 0.7 stars on average, and it costs no engineering time.

**Exactly what to change**

1. Name one owner and a daily 15-minute queue. The weekly digest lists every unanswered low-star review.
2. Write eight reply templates, one per major theme, that (1) name the specific problem, (2) say what the user can do today, (3) say which version fixes it. Retire "please contact your transport manager" as a standalone answer.
3. When a fix ships, reply again on the reviews that reported that problem. Play notifies the reviewer and invites them to update the rating.
4. Later: draft replies automatically from the theme and have a person approve them through the Play Developer Reply API.

**Tomorrow morning:** Two people, one day: reply to the low-star reviews of the last 90 days, lock-out and login first because there is a concrete workaround to give.

**Done when:** 95% of low-star reviews answered within 24 hours, every week.

#### A3. Let people skip the trip rating, and stop asking for Play reviews after every ride

- **Owner:** Product manager, rider app
- **Evidence:** 32 of 849 low-star reviews (4%), the last 12 months

This is the one complaint that is literally about ratings. People write that they came to give one star because the app would not let them see their next cab until they rated the last one. Others report the opposite problem: no way to rate or report a bad trip later, and a form that only accepts 4 or 5 stars. Both break trust in the number.

**Exactly what to change**

1. Add Skip. Never put trip details, the boarding OTP or tracking behind a rating screen.
2. Accept all five stars with reason chips, and allow rating or reporting a trip from trip history for 48 hours.
3. Ask for a Play Store review only through Google's In-App Review API, after an objectively good trip (on-time pickup, no issue raised), at most once a quarter per person. Remove custom "rate us" pop-ups.

**Tomorrow morning:** If the rating wall is server-configured, switch it off behind a flag today. Then verify the reports of low stars being rejected - if true, fix it before anything else on this list.

**Done when:** No new review in this theme for 30 days; in-app trip-rating response rate holds within 10% of today.

### Next 30 days

#### B1. Make sessions last and OTPs arrive

- **Owner:** Platform / auth team
- **Evidence:** 254 of 1,649 low-star reviews (15%), since January 2025

Getting logged out, or not getting the OTP, is the single biggest named reason for a low rating. It arrives in bursts that follow releases: January-February 2025, June 2025 and October 2025 each brought three to four times the usual monthly count. A commuter standing at a pickup point at 4 a.m. who cannot log in cannot see the cab number, the driver or the boarding OTP.

**Exactly what to change**

1. Refresh-token sessions that survive restarts, network drops and app updates. Re-authenticate at most every 30 days, or as the customer's SSO policy requires.
2. Never log out on a failed network call. Reviews describe being logged out by a tunnel or a basement car park.
3. OTP delivery with failover - SMS, WhatsApp, email, voice call - and a delivery-rate dashboard by provider and customer, with alerts.
4. Say plainly when a phone number or email is not registered instead of sending nothing.
5. Offline trip card: cache the next trip (cab number, driver, pickup time, boarding OTP) so a logged-out or offline user can still board.
6. Add login success rate to the release gate.

**Tomorrow morning:** Pull auth logs for the three incident windows: attempts versus successes by app version and customer. Find the session-expiry change that shipped around 13 June 2025.

**Done when:** Login success at or above 99.5%, OTP delivered within 30 seconds at the 95th percentile, and this theme under 5% of low-star reviews.

#### B2. Gate releases on the signals that produce 1-star reviews

- **Owner:** Release manager / QA
- **Evidence:** 81 of 849 low-star reviews (10%), the last 12 months

The app ships roughly every two weeks, and the share of 1-star reviews swings widely from one release to the next. The Play listing's "What's new" is empty, so users discover changes by surprise. Each bad release is visible in this data within days.

**Exactly what to change**

1. Staged rollout for every release with automatic halt criteria: crash-free sessions, login success, and the 1-star share from this pulse.
2. Test matrix that includes the next Android version before it ships, and the ten most-used devices.
3. UI changes behind flags, offered first as an opt-in beta to two or three customers.
4. Write real release notes on Play for every release.
5. Run the pulse daily for seven days after each release.

**Tomorrow morning:** Add the release table from this page to the release checklist, and write "What's new" for the build going out now.

**Done when:** No release with a 1-star share more than 8 points above the trailing baseline.

#### B3. Give ride complaints a home inside the app

- **Owner:** Product + customer operations
- **Evidence:** 186 of 849 low-star reviews (22%), the last 12 months

About one low-star review in five is about the ride, not the app: a late cab, a long route, a rude driver, a no-show marked unfairly, a helpdesk that does not pick up. Several say outright they are writing on Play Store because there is nowhere else. The app cannot fix a late cab, but it can make sure the complaint reaches someone who can.

**Exactly what to change**

1. "Report a problem with this trip" on the trip card and in history: late, wrong route, driver, no-show dispute, safety.
2. Route it to the customer's transport desk with an SLA timer, and show the employee the status.
3. No-show disputes carry the GPS trail automatically, so the decision is quick and fair.
4. When the helpdesk line is busy, offer a callback instead of a dead end.
5. Show booking rules in the app where they bite ("bookings close 8 hours before the shift, set by your employer").

**Tomorrow morning:** List the feedback endpoints that already exist, agree the five categories, and mock the entry point on trip history.

**Done when:** Ride-only complaints fall below 12% of low-star reviews; median first response on a trip issue under 30 minutes.

#### B4. Make live tracking believable

- **Owner:** Maps / tracking team
- **Evidence:** 95 of 849 low-star reviews (11%), the last 12 months

Tracking is what people open the app for, and it is the subject four and five-star reviewers mention most. The complaints are consistent: the map zooms out on its own every few seconds, the cab icon sits still for minutes, the ETA jumps from 5 minutes to 30, and the call-driver button does not connect.

**Exactly what to change**

1. Stop resetting the zoom after the user has zoomed in. The smallest change on this list and one of the most cited.
2. Show how old the position is ("updated 40s ago") and grey out a stale cab instead of showing a wrong one.
3. Smooth the ETA, and show how many pickups remain before mine.
4. Push "cab is 5 minutes away" and "cab has arrived" with sound.
5. Detect a driver app that has been force-stopped (no heartbeat) and tell the rider and the transport desk.
6. Fix call-driver, and add quick messages for when a call cannot connect.

**Tomorrow morning:** Ship the zoom fix.

**Done when:** Tracking under 5% of low-star reviews; ETA within 5 minutes for 80% of pickups.

### 60 to 90 days

#### C1. Pay back the redesign debt

- **Owner:** Product design
- **Evidence:** 157 of 849 low-star reviews (18%), the last 12 months

Reviewers say the new interface removed or hid things they relied on: who else is in the cab and in what order, the pickup time, the shuttle's position. They also report that booking a shuttle became two steps, that times show no AM or PM, and that editing a booking means cancelling it first.

**Exactly what to change**

1. Put co-riders, pickup order and pickup time back on the trip card.
2. Show AM/PM or a 24-hour clock everywhere a time appears.
3. One-step shuttle booking, and edit a booking without cancelling it.
4. Dark mode, and a way to message the driver.

**Tomorrow morning:** Run: python -m pulse show trip_info --since 2026-01-01. It is a short list of things people ask to have back, in their words.

**Done when:** Redesign and usability under 5% of low-star reviews.

#### C2. Remove the forced asks

- **Owner:** Product manager, rider app
- **Evidence:** 96 of 849 low-star reviews (11%), the last 12 months

Small frictions reviewers keep naming: the transport policy to accept on every launch, microphone permission demanded up front, a forced automatic time zone, full-screen banners before the cab details, the same notification ten times a day, and a slow cold start.

**Exactly what to change**

1. Ask for policy acceptance once per policy version, not once per launch.
2. Ask for the microphone only when a call starts. Do not require automatic time zone.
3. Notification preferences, and one notification per event.
4. No full-screen banner before trip details. Set a cold-start budget of 2 seconds to the trip card.

**Tomorrow morning:** Count the taps between opening the app and seeing the cab number on a fresh install.

**Done when:** These themes under 5% of low-star reviews combined.

#### C3. Fix the small listings, where a handful of reviews decides the score

- **Owner:** Driver-app product manager
- **Evidence:** see the other listings table

The driver onboarding app is rated on a few dozen ratings, the field app on fewer. Drivers report being stuck "in review" with no contact, and being unable to upload documents. With so few ratings, fixing and answering a dozen reviews moves the number. The same app also shows a lower score outside India, where few people have rated it.

**Exactly what to change**

1. Show onboarding status and the expected wait in the driver app; fix document upload.
2. Reply to every review on the three small listings - there are fewer than 130 in total.
3. Track the US, Philippines and UK scores in the weekly digest.

**Tomorrow morning:** Reply to the seven written reviews on the Driver Partner listing.

**Done when:** Driver Partner listing at 4.0 or above.

## What the plan should be worth

| Scenario | Low-star reviews avoided per year | One-star share of ratings | Public score |
|---|---|---|---|
| Today | 0 of 849 | 6.4% | 4.64 |
| This week | 61 | 6.0% | 4.65 |
| Plus next 30 days | 246 | 4.6% | 4.71 |
| Whole plan | 358 | 3.9% | 4.74 |

An estimate built on stated assumptions (see `pulse/plan.py`), not a forecast. Replies come on top: Google reports an average lift of 0.7 stars on a negative review that gets one.

## Why people rate 1 to 3 stars

Low-star reviews, last 12 months (n = 849). A review can carry more than one reason.

| Reason | Reviews | Share | Owner |
|---|---|---|---|
| Generic verdict, no detail ("worst app") | 157 | 18% | No detail given |
| Login, OTP or being logged out | 111 | 13% | App engineering |
| Booking, schedule, roster or cancellation blocked | 76 | 9% | App engineering |
| Live tracking, cab location or ETA wrong | 70 | 8% | App engineering |
| Helpdesk unreachable / complaints go nowhere | 64 | 8% | Ride operations |
| Confusing or hard-to-use interface | 59 | 7% | Product decisions |
| Slow, laggy, network or battery heavy | 55 | 6% | App engineering |
| Route, clubbing, pickup time or pickup point | 52 | 6% | Ride operations |
| Cab late, not assigned, or unfair no-show | 49 | 6% | Ride operations |
| "Not working", errors, bugs (no specifics) | 46 | 5% | App engineering |
| App crashes, freezes or will not open | 38 | 4% | App engineering |
| "The new update / new UI made it worse" | 35 | 4% | Product decisions |
| Trip details hidden: cab number, co-riders, pickup time, history | 32 | 4% | Product decisions |
| Service / vendor / employer transport policy in general | 30 | 4% | Ride operations |
| Calling or chatting with driver / co-riders fails | 27 | 3% | App engineering |
| Notification / alert spam, ads, or missing alerts | 26 | 3% | Product decisions |
| Driver behaviour, vehicle condition, safety | 25 | 3% | Ride operations |
| "Not installed from Play Store" lock-out, forced reinstall | 22 | 3% | App engineering |
| Forced permissions, repeated policy pop-up, privacy | 19 | 2% | Product decisions |
| Boarding step: QR scan, trip OTP, seat-belt check, check-in | 16 | 2% | App engineering |
| Forced trip rating / nagging for ratings | 16 | 2% | Product decisions |
| No way to rate / report a trip in the app (or low stars blocked) | 16 | 2% | Product decisions |
| Non-commute modules: parking, desk, meal, metro | 2 | 0% | Product decisions |

The live page (`docs/index.html`) has the charts, the release table, the reply history and the method.

# Orbit Mini — end-of-day report

**Built:** Monday 21 – Tuesday 22 September 2026
**Live:** https://orbit.ehnand.com
**Code:** https://github.com/blank0810/orbit-mini

---

## 1. Against the brief

| # | Asked for | Status |
|---|---|---|
| R1 | Sign up to a monthly plan through Stripe, test mode | **Done** |
| R2 | The system records the payment | **Done** |
| R3 | One page shows that person their plan and status | **Done** |
| R4 | Laid out properly on a phone | **Done** |
| R5 | A small FastAPI service behind it | **Done** |
| R6 | One database table | **Done, with a caveat — see §4** |
| R7 | Tests for the sign-up and the payment webhook | **Done** |
| R8 | A Dockerfile | **Done** — two, plus compose |
| R9 | Looks like it belongs on scalesage.ai | **Done** |
| R10 | Hosted locally, tunnelled via Cloudflare, on a real domain | **Done** |
| R11 | A small Flutter component | **Done** — package, widget gallery, running on a real handset |
| R12 | FFmpeg processing with a Runpod integration | **NOT BUILT** |
| D1 | A link to the code | Done |
| D2 | This report | Done |
| D3 | A video under five minutes | **Done** — 1m37s, narrated, captioned, embedded on the site |

**One of fifteen is not delivered: R12.** Nothing in the pass/fail core is missing.

---

## 2. Hours

I cannot give you a single honest number, so here is the method and a range.

The repository has 39 commits spanning **30h58m** wall-clock, of which **9h05m** was a
single overnight break. Clustering commits into working sessions, and crediting 25 minutes
of lead-in before each session's first commit:

| A gap shorter than this counts as work | Credited | Sessions |
|---|---|---|
| 45 minutes | 9h25m | 11 |
| 90 minutes | 11h23m | 8 |
| 120 minutes | 13h47m | 6 |

**Call it 10 to 12 hours.** The 45-minute figure is certainly too low: the test suite
landed as a single commit and is 844 lines plus a mutation-testing pass, which was not 25
minutes of work. The 120-minute figure is too generous — it credits six sessions with
their full internal gaps, including time spent waiting on container builds and a 97-second
video render.

I have not rounded either bound to flatter the result, and the commit history is in the
repository if you want to check the arithmetic.

Roughly a third of that time went to work the brief did not ask for. See §3.

---

## 3. Built beyond the brief, deliberately

Each of these was a decision, not drift. They are recorded in `AGENTS.md` §11.

**Accounts and login.** The brief asks for no authentication. Without it,
`GET /api/subscribers/{email}` on a public domain hands any caller any customer's billing
status by guessing an address. For a role maintaining a *client* dashboard that seemed
worth the two hours. Argon2id hashing, a stateless JWT in an httpOnly cookie.

**Two plans instead of one**, Starter £597 and Pro £1,497, matching scalesage.ai's real
pricing page. Ranked rather than listed: Pro carries the recommended marker, as on your site.

**Switching plans and cancelling.** A client dashboard whose only verb is "buy" is a
checkout page. Switching repoints the existing Stripe subscription rather than opening a
second one; cancelling is scheduled for the end of the paid period and stays reversible
until that date.

**A one-click demo account**, capped at five with oldest-out eviction, so you can look at a
populated dashboard without registering.

**Separate development and production stacks.** They were originally one, sharing a
database. Now `orbit-dev` and `orbit-prod` have their own containers, networks and volumes.

---

## 4. Where I have been imprecise, corrected

**"One database table" is one domain table, not one table.** `subscriber` holds everything
about a customer. Alembic also maintains `alembic_version`, a single-column table recording
which migration has run. That is migration bookkeeping rather than application data, but
`\dt` shows two rows and you should hear that from me rather than find it.

Idempotency is handled by a `last_stripe_event_id` column rather than an events table,
which is what kept the domain model to one table.

---

## 5. Known gaps

Ordered by how much they would matter in production.

**No FFmpeg/Runpod pipeline (R12).** Not started, and simply absent — there is no partial
implementation to review. It is the one scored item I did not reach.

**The Flutter component (R11) is a component, not an Android home-screen widget.** Worth
saying plainly, because "widget" means two different things. `mobile/orbit_status_card/` is
a Dart package exposing `OrbitStatusCard`, with a gallery that renders all nine states with
no server running, and an example app that signs in against the live API. It is installed
and running on a physical Galaxy A35 — that is the phone in the video. A launcher widget
would have to be Kotlin and RemoteViews, which would demonstrate less Flutter, not more.

**The video's narration is synthetic, and the voice is not the one originally chosen.**
ElevenLabs, voice *Alice* (British female). The voice first picked is a library voice and
the API refuses those without a paid plan; Alice was the nearest usable match. The prior
take was Kokoro-82M generated locally and is kept in `vo/kokoro-backup/`. Details and the
one-command swap: `brag-output-*/REPLACING-THE-VOICE.md`.

**Registration discloses whether an email has an account.** `POST /api/auth/register`
answers 409 for an address already in use. Login does *not* leak this — it returns an
identical 401 for an unknown email and a wrong password, and still runs a hash verification
when the account is absent so the timing does not differ either. Closing it on registration
needs the email flow that was cut; suppressing the conflict without email would tell a real
person their signup worked when it did not.

**No password reset, email verification, or login rate limiting.** A login without a reset
flow is incomplete. The demo account's password is printed on the sign-in page, which
covers the demo but not a real user.

**The idempotency guard only catches consecutive replays.** `last_stripe_event_id` stores
one id. Stripe retries the same event, which this handles. An out-of-order redelivery —
event A, then B, then A again — would reapply A. Fixing it properly needs a second table
or another column; the brief's one-table constraint is why it stands as it is.

**A deploy has a brief window where new code meets the old schema.** The image rebuild and
the migration are sequential, so for a few seconds new code runs against the old database
shape. At this traffic level that is seconds of exposure; a busy system would add the
column in a prior release.

**No resync command.** If a webhook delivery is ever missed, there is no way to re-read a
subscriber's state from Stripe short of doing it by hand. I did exactly that once, by hand,
after finding the billing-period bug.

**The prorated plan switch has not run against a real subscription.** Every error path is
tested and the happy path is covered by the suite with Stripe stubbed, but no real card has
been switched between plans.

---

## 6. Three bugs worth telling you about

Both were invisible to code review and both were found only by running the thing.

**`stripe.Event` is not a mapping.** The webhook verified signatures correctly and then
died converting the event to a dict, because stripe-python 15.x returns an object that is
neither iterable nor a mapping. The endpoint returned 500 on every valid payment. Found by
firing a real signed payload at it, not by reading the code.

**A Checkout session carries no billing period.** `checkout.session.completed` set the
status to active and left `current_period_end` NULL, so the dashboard showed "Active" with
a blank renewal date after a real payment. The subscription object holds the period, not
the session. Found when the operator made a real payment and looked at the result.

**A Subscription is not a mapping either — the same root cause, found on submission day.**
Switching plans returned 500. `change_subscription_price` probed the retrieved
subscription with `.get("items", {})`, and a `Subscription`, like an `Event`, defines
`__getitem__` but not `.get()`, so it raised `AttributeError` rather than returning the
default. It failed on the one endpoint that moves a customer's money.

That it is the *same* mistake twice is the part worth reporting. The cause was a gap in
how the suite is built: every test stubs `stripe_client`'s **functions**, which is what
keeps the suite offline, but it also means the module's own body never executes. Both bugs
lived in that body.

`tests/test_stripe_client.py` now stubs one level lower — at `stripe.Subscription.retrieve`
and `.modify` — and returns real `StripeObject` instances built with `construct_from`,
which is a local constructor and makes no network call. Stubbing with plain dicts there
would have kept the suite green while production kept failing, which is exactly how this
shipped in the first place.

All three now have regression tests. I verified this one against the live test-mode
subscription rather than trusting the fix: the old expression still raises on a real
`Subscription`, the new one reads the item, and a full Pro → Starter → Pro round trip
leaves our row and Stripe in agreement.

---

## 7. What is running

```
orbit-dev    web :7301  api :7302  db :7303  pgadmin :7304
orbit-prod   web :7311  api :7312  db :7313  pgadmin :7314   + Cloudflare Tunnel
```

Every port binds to `127.0.0.1`. The tunnel dials out and holds the connection open, so no
inbound port is forwarded on the router. pgAdmin runs but has no ingress rule, which is what
keeps a database admin UI off the public internet — it is unroutable rather than firewalled.

43 tests, 1505 lines of API code, 844 lines of tests, 1310 lines of front-end.

```bash
make            # every command, with descriptions
make test       # the suite; no network, no Stripe keys
make deploy     # test, build, migrate, then verify the public url
```

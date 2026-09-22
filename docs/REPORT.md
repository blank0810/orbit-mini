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
| R11 | A small Flutter component | **NOT BUILT** |
| R12 | FFmpeg processing with a Runpod integration | **NOT BUILT** |
| D1 | A link to the code | Done |
| D2 | This report | Done |
| D3 | A video under five minutes | **NOT DONE** |

**Three of fifteen are not delivered.** They are the last three in the list and they are
the two range items plus the video. Nothing in the pass/fail core is missing.

---

## 2. Hours

I cannot give you a single honest number, so here is the method and a range.

The repository has 30 commits spanning **25h17m** wall-clock, of which about **9h** was an
overnight break. Clustering commits into working sessions, and crediting 25 minutes of
lead-in before each session's first commit:

| A gap shorter than this counts as work | Credited |
|---|---|
| 45 minutes | 7h15m |
| 90 minutes | 8h35m |
| 120 minutes | 9h46m |

**Call it 8 to 10 hours.** The 45-minute figure is certainly too low: the test suite landed
as a single commit and is 844 lines plus a mutation-testing pass, which was not 25 minutes
of work. The 120-minute figure is probably too generous.

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

**No Flutter component (R11) and no FFmpeg/Runpod pipeline (R12).** Not started. These are
the two range items and they are simply absent — there is no partial implementation to
review. The time went into subscription management instead, which was my call to make and
is the main thing I would do differently.

**No video (D3).** Not recorded.

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

## 6. Two bugs worth telling you about

Both were invisible to code review and both were found only by running the thing.

**`stripe.Event` is not a mapping.** The webhook verified signatures correctly and then
died converting the event to a dict, because stripe-python 15.x returns an object that is
neither iterable nor a mapping. The endpoint returned 500 on every valid payment. Found by
firing a real signed payload at it, not by reading the code.

**A Checkout session carries no billing period.** `checkout.session.completed` set the
status to active and left `current_period_end` NULL, so the dashboard showed "Active" with
a blank renewal date after a real payment. The subscription object holds the period, not
the session. Found when the operator made a real payment and looked at the result.

Both now have regression tests.

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

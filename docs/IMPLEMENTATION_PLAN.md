# Orbit Mini, Implementation Plan

**Status:** scaffolded, not started
**Written:** 2026-09-21
**Stated deadline:** Monday 2026-09-21 (today)
**Target start date being gated on it:** Wednesday 2026-09-23

---

## 0. The brief, decomposed into scored items

Every line below maps to a sentence in the brief. Nothing here is invented scope.

| # | Requirement | Tier |
|---|---|---|
| R1 | Someone signs up to a monthly plan through Stripe, test mode | P0 |
| R2 | The system records the payment | P0 |
| R3 | One page shows that person their plan and status | P0 |
| R4 | That page is laid out properly on a phone | P0 |
| R5 | A small FastAPI service behind it | P0 |
| R6 | One database table | P0 |
| R7 | Tests for the sign-up and the payment webhook | P0 |
| R8 | A Dockerfile | P0 |
| R9 | Looks like it belongs on scalesage.ai, not a default template | P0 |
| R10 | Hosted locally, tunnelled via Cloudflare, on an accessible domain | P0 |
| R11 | A small Flutter component (maps to their Orbit mobile app) | P1 |
| R12 | FFmpeg processing with a Runpod API integration (maps to Content Factory) | P1 |
| D1 | A link to the code | P0 |
| D2 | A written end-of-day report: hours spent, anything unfinished | P0 |
| D3 | A video under 5 minutes showing it working | P0 |

**P0 is the pass/fail core. P1 is the range demonstration.** If time runs out, P1 gets cut
and named in D2, which the brief explicitly asks for. A truthfully-reported gap scores
better than a broken P0.

---

## 1. Decisions already made

These are settled. Do not relitigate them mid-build.

### 1.1 FastAPI is the system of record, Next.js is the client

The brief mandates FastAPI. Next.js exists to satisfy R3, R4 and R9, and it calls the API
over HTTP. No database access, no Stripe secret, no business logic in `web/`.

Taking the shortcut of doing the payment work in a Next.js route handler is the exact thing
the brief is testing for. It would fail R5 while appearing to work.

### 1.2 Cloudflare Tunnel, not Vercel

The brief says: *"Host it locally, tunnel it out via Cloudflare, and deploy it to an
accessible domain, we want to see the DevOps/Docker/sysadmin side directly, not just hear
about it."*

Vercel would delete the thing being scored. It would hide the Dockerfile (R8), hide the
compose orchestration, and hide the sysadmin work, and it would do so while directly
contradicting an instruction. A reviewer who asked for a tunnel and received a Vercel URL
reads that as either not reading the brief or not being able to do the infrastructure.

Target: `orbit.ehnand.com`, a named Cloudflare Tunnel into a local `docker compose` stack.
The domain and a working tunnel already exist on this machine, so this is configuration,
not new infrastructure.

### 1.3 Stripe Checkout, hosted, not a custom card form

Fastest path to R1, and the correct one. No card data touches our stack, so there is no PCI
surface to defend in the report. Subscription mode, one monthly price, test mode throughout.

### 1.4 One table means one table

`subscriber` holds identity, the Stripe ids, the plan, the status and the timestamps.
No separate users, subscriptions, or events tables. R6 is literal.

Idempotency is handled by storing the last processed Stripe event id on the row, not by
adding a second table. This is the YAGNI-respecting version of the guarantee.

### 1.5 Postgres, not SQLite

Compose already needs a service, the reviewer is scoring infrastructure, and a real database
in a real container is the point. Schema is created by a single Alembic migration so the
deploy story is honest.

---

## 2. Data model

One table, `subscriber`:

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, pk | |
| `email` | text, unique, not null | the login identity |
| `first_name` | text, not null | |
| `last_name` | text, not null | |
| `password_hash` | text, not null | argon2. Never logged, never returned in any response. |
| `stripe_customer_id` | text, nullable, indexed | set on checkout creation |
| `stripe_subscription_id` | text, nullable, indexed | set on webhook |
| `plan_name` | text, not null | denormalised for display, avoids a Stripe call per page load |
| `status` | text, not null | `incomplete` on signup, then mirrors Stripe |
| `current_period_end` | timestamptz, nullable | |
| `last_stripe_event_id` | text, nullable | the idempotency guard |
| `created_at` / `updated_at` | timestamptz | |

`status` values, mirrored from Stripe, never invented locally:
`incomplete`, `active`, `past_due`, `canceled`.

---

## 3. API surface

Deliberately small. Four endpoints plus health.

| Method | Path | Does |
|---|---|---|
| `GET` | `/api/health` | liveness. Touches no database. |
| `GET` | `/api/health/ready` | readiness, `SELECT 1`. What the compose healthcheck polls. |
| `POST` | `/api/auth/register` | create the account: first name, last name, email, password. Status `incomplete`. |
| `POST` | `/api/auth/login` | verify the password, set the signed httpOnly cookie |
| `POST` | `/api/auth/logout` | clear the cookie |
| `POST` | `/api/checkout` | **authenticated.** Create a Stripe Checkout session, return its URL |
| `POST` | `/api/webhooks/stripe` | verify signature, apply idempotently, return 2xx fast |
| `GET` | `/api/subscribers/me` | **authenticated.** Plan, status, period end |

**`/api/signup` is gone, split in two.** With accounts, signing up and paying are separate
acts: `register` creates the person, `checkout` sells them the plan. Required test 1 splits
the same way — register creates exactly one row, checkout returns a Stripe URL.

The webhook stays unauthenticated. Stripe's signature *is* its authentication, and Stripe
cannot present a cookie.

No admin routes, no list endpoint, no pagination, no password reset. Reset is a real gap and
is named in the report rather than quietly skipped.

### Webhook events handled

- `checkout.session.completed`, records the payment, sets `active`, stores the subscription id
- `customer.subscription.updated`, mirrors status and period end
- `customer.subscription.deleted`, sets `canceled`

Everything else is acknowledged with 200 and ignored. Unknown event types are not errors.

---

## 4. Phases

Ordered so that the pass/fail core is standing before anything optional starts.
Estimates are working hours, honest, not optimistic.

### Phase 1, API core (~3h) `P0`
1. `uv` project, FastAPI app factory, settings via pydantic-settings, `.env.example`.
2. SQLAlchemy 2.0 `Subscriber` model, one Alembic migration.
3. `POST /api/signup`: validate, upsert, create Stripe Checkout session, return URL.
4. `POST /api/webhooks/stripe`: signature verification, idempotency check against
   `last_stripe_event_id`, the three handlers, fast 2xx.
5. `GET /api/subscribers/{email}`.

**Gate:** `stripe listen --forward-to localhost:7302/api/webhooks/stripe`, run a real test
checkout, and read the row out of Postgres. Do not proceed on belief.

### Phase 2, tests (~1.5h) `P0` R7
Written alongside Phase 1, not after it. The four required cases from `AGENTS.md` section 5:
sign-up creates one row and returns a URL, valid-signature webhook activates, invalid
signature is rejected with 400 and writes nothing, replayed event is idempotent.

Stripe stubbed at the boundary. Transactional fixture against a real Postgres.

**Gate:** `uv run pytest -q` passes, and you read the output.

### Phase 3, the dashboard (~2.5h) `P0` R3 R4 R9
Mobile-first at 390px. Three views:
- **Pricing / signup:** one plan, one primary action. Hick's Law says one plan means the
  decision is yes or no, so do not build a comparison table.
- **Pending:** the state between redirect and webhook arrival. Doherty Threshold: this wait
  exceeds 400ms by design, so it gets an explicit skeleton and a polled status, never a dead
  screen.
- **Dashboard:** identity, plan, status, period end, billing action. Grouped into three
  regions by proximity, not by dividers. Status carries an icon and a label, never colour alone.

Design direction: pull the palette, type and density from `scalesage.ai` so R9 is satisfied
by resemblance to their actual product, not by generic polish. Delete the Next.js boilerplate
page, the Vercel SVGs and the default favicon before anything else.

**Gate:** 390x844 screenshot, full keyboard tab pass, contrast check at 4.5:1.

### Phase 4, Docker and compose (~1h) `P0` R8
- `api/Dockerfile`: multi-stage, non-root user, no build toolchain in the final image.
- `web/Dockerfile`: Next.js standalone output.
- `infra/docker-compose.yml`: `db`, `api`, `web`, healthchecks, named volume, one `.env`.

**Gate:** `docker compose up --build` from a clean checkout plus `.env` produces a working
system. Test it by actually removing the volume first.

### Phase 5, Cloudflare Tunnel (~1h) `P0` R10
Named tunnel, DNS route to `orbit.ehnand.com`, ingress rules sending `/api/*` to the API
and everything else to the web container. Those targets are `api:8000` and `web:3000` if
`cloudflared` runs as a compose service, or `localhost:7302` and `localhost:7301` if it runs
on the host. **Open decision, see the note at the end of this section.** No extra reverse proxy: cloudflared's own path routing is
enough, and a second proxy is a component with no job.

Then point the **Stripe webhook endpoint at the public URL**, not at `stripe listen`. This is
the moment the infrastructure story becomes real rather than claimed, and it is worth saying
so in the report.

**Gate:** open `https://orbit.ehnand.com` from a phone on mobile data. Complete a test
checkout end to end over the public URL and watch the status flip.

### Phase 6, Flutter component (~1.5h) `P1` R11
One widget, not an app: a subscription status card that calls
`GET /api/subscribers/{email}` and renders plan, status and period end, with loading, error
and empty states. Same status vocabulary and the same visual language as the web dashboard,
which is the point being demonstrated: one API, two clients, consistent contract.

**Gate:** runs, screenshot or screen recording captured for the video.

### Phase 7, FFmpeg plus Runpod (~2h) `P1` R12
A standalone worker in `media/`:
1. Take an input video.
2. FFmpeg: normalise, extract a segment or thumbnail, transcode to a delivery format.
3. Submit a job to the Runpod API, poll for completion, handle failure and timeout.
4. Write the output and log the timings.

The integration discipline is what is scored, not the effect: async job submission, polling
with backoff, and explicit handling of the failure path. Note which failures are safe to
retry and which are not.

**Gate:** run it on a real sample file and keep the output for the video.

### Phase 8, deliverables (~1.5h) `P0` D1 D2 D3
1. **README.md** written for the reviewer: what it does, how to run it, the decisions and
   their tradeoffs, what is not built and why.
2. **End-of-day report**: hours spent per phase, what is finished, what is unfinished, stated
   flatly. The brief asked for the unfinished list, so it is a scored answer, not a confession.
3. **Video, under 5 minutes.** Suggested cut: signup on a phone (40s), Stripe test checkout
   (30s), the status flipping live on the webhook (40s), the public URL and the tunnel
   (30s), `docker compose up` and the passing test suite (45s), Flutter card (30s), FFmpeg
   plus Runpod run (40s). Show it working. Do not narrate architecture over a static screen.

---

## 5. Total and the timeline problem

| Tier | Hours |
|---|---|
| P0 (Phases 0 to 5, 8) | ~13 |
| P1 (Phases 6, 7) | ~3.5 |
| **Total** | **~16.5** |

Up from 14: accounts and login add ~2h across the API, the UI and the tests, and Phase 0
below adds ~0.5h of structure that Phase 4 no longer has to do.

### Phase 0, containers and the layered skeleton (~1.5h) `P0`
Moved ahead of Phase 1 by operator decision: containerise the layered structure before any
feature exists, so every later phase is written inside a stack that already runs.

Every layer folder from `docs/ARCHITECTURE.md` created with an `__init__.py` that names what
the layer owns. Real code for `core/config.py`, `db/session.py`, `db/base.py`,
`controllers/health_controller.py` and `routes/api_router.py` only. No model, no Stripe, no
auth yet.

**Gate:** `docker compose up --build` brings up db, api and web; `/api/health` returns 200
without touching the database and `/api/health/ready` returns 200 having run `SELECT 1`
against Postgres. The second one is what proves the db layer is wired, not assumed.

**The stated deadline is today.** Fourteen hours does not fit in what is left of it. The
realistic options, in order:

1. **Ship P0 tonight, name P1 as unfinished in the report.** The brief asks for the
   unfinished list, so this is a supported outcome rather than a failure. The core is
   complete, public and tested.
2. **Ask Cy for Tuesday.** One short message, no apology, no explanation of why. Reasonable
   given a brief this size arrived with a weekend-to-Monday turnaround, and it gates a
   Wednesday start that Tuesday still clears.
3. Ship everything, badly. Not an option. A broken P0 scores worse than an honest partial.

Decide between 1 and 2 before starting Phase 1, because the answer changes how much of P1
gets attempted.

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| Webhook never arrives, status never flips | Verify with `stripe listen` in Phase 1 before any UI exists. Do not discover this in Phase 5. |
| Tunnel works locally, fails from mobile data | Test from a phone off wifi, not from a second browser tab. |
| Runpod key or quota unavailable | Confirm credentials in the first 15 minutes of Phase 7. If unavailable, stop and report it as blocked rather than burning two hours. |
| Next.js default template leaks into the submission | Delete boilerplate in the first 10 minutes of Phase 3, before styling anything. |
| Flutter toolchain cold start eats the budget | `flutter doctor` before Phase 6 starts, not during. |
| Demo fails on camera | Record after a full clean `docker compose down -v && up --build` rehearsal. |

---

## 7. Scope discipline

Explicitly **not** building, and saying so in the report if asked:

### The demo account

A seeded, already-`active` account whose credentials are shown on the login page.

**Why.** Without it the reviewer must register, then complete a Stripe test checkout, before
seeing a single dashboard. One button instead removes that entirely. It also covers the gap
below: nobody needs a password reset for an account whose password is printed on the page.

- `demo@orbit.ehnand.com`, "Demo Account", status `active`, `stripe_subscription_id`
  `sub_demo_seeded`. Unmistakably seeded, never mistakable for a real webhook result.
- Created by `docker compose exec api python -m app.seed_demo`, documented in `README.md`.
  Not an `ENVIRONMENT`-conditional branch on boot: that is a config knob, and every knob is a
  decision someone makes later under pressure.
- The login page gets ONE "Use demo account" button that fills both fields, with the
  credentials in plain text beneath it as information. Not a button *and* a copy affordance
  competing for the same job.
- The demo is the fast path, not the proof. The video still shows a real registration, a real
  test checkout, and the status flipping on a real webhook.

### Still not built

- **Password reset, email verification, OAuth, "remember me", rate limiting on login.**
  Accounts are in (see `AGENTS.md` section 11); the rest of an auth system is not. Named in
  the report as the known gap, because a login without a reset flow is incomplete and
  pretending otherwise fails on the reviewer's first question.
- Multiple plans or tiers. One monthly plan.
- Admin dashboard, user list, or reporting.
- Email notifications.
- CI. There is no CI requirement in the brief. Tests run locally and in compose.
- Kubernetes, Terraform, or any orchestration beyond compose.

Each of those is a feature someone would have to maintain, added to satisfy nobody's stated
requirement. YAGNI.

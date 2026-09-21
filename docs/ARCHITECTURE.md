# Architecture

The layer contract from [`AGENTS.md`](../AGENTS.md) section 3.3, applied to all four
surfaces. `AGENTS.md` governs; this file is the detail.

---

## 1. The rule that shapes everything

**Every external service gets exactly one module that talks to it.** Nothing else imports
it, nothing else knows its address.

| Boundary | The only file allowed through |
|---|---|
| Stripe | `api/app/services/stripe_client.py` |
| Postgres | `api/app/db/session.py` |
| The API, from web | `web/src/lib/api/client.ts` |
| The API, from Flutter | `mobile/…/services/subscriber_service.dart` |
| Runpod | `media/services/runpod_client.py` |

Two things follow. The required tests become writable, because there is one thing to stub
rather than twelve. And the boundary in `AGENTS.md` section 2 stops being a promise and
becomes a structural fact: `web/` cannot reach the database because nothing in `web/` can
import a database.

## 2. Why a monorepo

The brief asks for **one link to the code**, covering four surfaces. Splitting them across
four repositories would mean four links, four clone steps, and a reviewer reassembling the
system by hand.

---

## 3. `api/` — owns all state, money and truth

```
api/
├── pyproject.toml  uv.lock  Dockerfile  .dockerignore  alembic.ini
├── alembic/versions/0001_create_subscriber.py
└── app/
    ├── main.py                        app factory, middleware, router mount
    │
    ├── core/
    │   ├── config.py                  pydantic-settings. The only reader of the env.
    │   └── exceptions.py              domain errors, mapped to HTTP at the edge
    │
    ├── db/
    │   ├── base.py                    DeclarativeBase
    │   └── session.py                 engine, session factory, get_session dependency
    │
    ├── models/
    │   └── subscriber_model.py        the ORM class. The one table.
    │
    ├── repositories/
    │   └── subscriber_repository.py   every query touching subscriber
    │
    ├── schemas/
    │   ├── signup_schema.py           signup request / response
    │   └── subscriber_schema.py       dashboard response
    │
    ├── services/
    │   ├── subscription_service.py    signup, status read
    │   ├── webhook_service.py         verify, idempotency, apply
    │   └── stripe_client.py           the Stripe SDK boundary
    │
    ├── controllers/
    │   ├── signup_controller.py       POST /api/signup
    │   ├── subscriber_controller.py   GET  /api/subscribers/... (see note)
    │   ├── webhook_controller.py      POST /api/webhooks/stripe
    │   └── health_controller.py       GET  /api/health
    │
    └── routes/
        └── api_router.py              mounts each controller under its prefix
```

### Why `repositories/` exists

Laravel's Eloquent is Active Record: the model *is* the query interface, so `User::where()`
lives on the model. SQLAlchemy 2.0 is Data Mapper: the model declares the table, the session
runs the query. Forcing Active Record onto it means fighting the ORM.

So the same two responsibilities are kept, split the way this ORM expects.
`subscriber_model.py` declares; `subscriber_repository.py` queries.

### Why `webhook_service.py` is its own file

It is the only code that mutates money state, and the only code a security reviewer reads
line by line: signature verification, the idempotency guard, three event handlers. Isolating
it means "the dangerous file" is one file.

### Resolved: real accounts

**Decided by the operator.** Not the signed-link alternative below, and not `{email}` in the
path: first name, last name, email and password, with a login.

New files, all inside the closed layer list:

```
core/dependencies.py                 get_current_subscriber, reads the cookie
services/auth_service.py             hash, verify, issue and decode the JWT
controllers/auth_controller.py       register · login · logout
schemas/auth_schema.py               register and login request shapes
```

`password_hash` is a column on `subscriber`, so R6's one table survives. The session is a
**stateless signed JWT in an httpOnly cookie** — a sessions table would be a second table.

The rule that does not bend: the password hash is never returned by any response and never
logged. `subscriber_schema.py` is the only shape the dashboard ever sees, and it has no
password field to accidentally populate.

### Superseded: the signed-link alternative

`docs/IMPLEMENTATION_PLAN.md` section 3 specifies `GET /api/subscribers/{email}`. That works,
and it is what the brief's wording supports, but on a public domain it means anyone can type
any address and read that customer's plan, status and billing date.

The alternative is one extra column, `access_token`: a random opaque string minted at signup
and carried in the Stripe success redirect, read back as `GET /api/subscribers/me?token=...`.
No password, no login screen, no account — just an unguessable link, the same model as a
Stripe receipt.

**Not decided by the operator yet.** Until it is, the controller is written against whichever
the plan says, and the layer shape is identical either way: the token check belongs in
`subscription_service.py`, not in the controller and not in the repository.

### `stripe_client.py`, never `stripe.py`

A module named `stripe.py` shadows the installed `stripe` package and breaks the import from
inside the package itself. Small, and genuinely nasty to debug.

### A request, end to end

```
POST /api/signup
  └─ routes/api_router.py          matches the path
     └─ signup_controller.py       Pydantic validates the body, calls one service
        └─ subscription_service.py the business rule: upsert, never downgrade an
           │                       active subscriber back to incomplete
           ├─ subscriber_repository.py   find / create the row
           └─ stripe_client.py           create the Checkout session
```

The controller holds no rules. The service touches no SQL and no HTTP. The repository knows
nothing about Stripe.

---

## 4. `web/` — presentation only

```
web/src/
├── app/
│   ├── layout.tsx  globals.css      design tokens as CSS custom properties
│   ├── page.tsx                     pricing / signup
│   ├── pending/page.tsx             the wait between redirect and webhook
│   └── dashboard/page.tsx
│
├── components/
│   ├── pricing/                     PlanCard · SignupForm
│   ├── dashboard/                   PlanSummary · StatusBadge · ActivityCard
│   └── ui/                          Button · Card · Field
│
└── lib/
    ├── api/
    │   ├── client.ts                base URL, fetch wrapper, error handling
    │   ├── payments.ts              createCheckoutSession
    │   └── subscribers.ts           getSubscriber, the polling read
    └── types.ts                     the contract, shared across both
```

Components are grouped by feature, not by kind. `ui/` holds only what is genuinely shared by
both features. The API is split by purpose — anything that starts a payment in `payments.ts`,
anything that reads in `subscribers.ts` — over a single `client.ts` so the base URL and the
error handling live in exactly one place.

**Fetching happens in the browser, not in the Next.js server.** Inside Docker the containers
reach each other as `http://api:8000`, but a browser cannot resolve `api`. Fetching client-side
means one address and one environment variable instead of two. It is also what the design needs:
the pending screen polls for the status flip while waiting on the webhook, and polling is
inherently client-side.

---

## 5. `mobile/` — a widget, not an app

A subscription status card. If ScaleSage's Orbit app had a "your subscription" card on its home
screen, this is that card.

```
┌──────────────────────────────┐
│ ● ACTIVE                     │
│                              │
│ ScaleSage Starter            │
│ £597 /mo                     │
│                              │
│ Renews 21 Oct 2026           │
└──────────────────────────────┘
```

It calls the same `GET /api/subscribers/me` the web dashboard calls, and carries loading, error
and empty states. No login, no navigation, no second app.

```
mobile/orbit_status_card/
├── pubspec.yaml
├── lib/
│   ├── orbit_status_card.dart              the public export
│   └── src/
│       ├── models/subscriber_model.dart
│       ├── services/subscriber_service.dart    the API boundary
│       └── widgets/
│           ├── status_card.dart
│           ├── status_badge.dart
│           └── status_states.dart          loading · error · empty
└── example/lib/main.dart                   a tiny host app to run it
```

It is a package rather than an application because the brief says *component*, and because a
package says "this could drop into Orbit" where an app says "I built a second app."

**What it demonstrates:** one API, two clients, one contract. Not Dart syntax — that the backend
and the mobile app will not drift apart.

---

## 6. `media/` — standalone

Imports nothing from `api/`. It is a separate worker that happens to live in the same repository.

```
media/
├── pyproject.toml  main.py            CLI entrypoint
├── models/job_model.py                job state and timings
└── services/
    ├── ffmpeg_service.py              local media operations
    ├── transcription_service.py       orchestrates the pipeline
    └── runpod_client.py               the Runpod boundary
```

Pipeline: video in, strip the audio with FFmpeg, submit to Runpod, poll with backoff, burn the
transcript back on as subtitles, video out. The scored part is the polling, the timeout, the
failure path, and knowing which failures are safe to retry.

---

## 7. `infra/`

```
infra/
├── docker-compose.yml                 db · api · web, healthchecks, named volume
├── cloudflared/config.yml             ingress rules (credentials are gitignored)
└── DEPLOY.md                          the tunnel runbook
```

### Ports

`7301` web, `7302` api, `7303` postgres, every one bound to `127.0.0.1`.

Not 3000/8000/5432: all three are already claimed by other projects on the build machine, and
the 7xxx range is clear and far from the ephemeral range. Loopback-only because `cloudflared`
runs on the host and reaches them over localhost, and `AGENTS.md` section 6 says treat every
endpoint as hostile-facing once the tunnel is up.

---

## 8. What this costs

About 22 files in `api/app/` where a flat layout needs 8, and several of them under 30 lines.

That is the price of the convention, paid on purpose. The same vocabulary appears in Python,
TypeScript and Dart, so a reviewer opening any of the four surfaces finds the same shape. For a
codebase whose next maintainer arrives from Laravel and NestJS, that is worth more than a
smaller file count.

# Orbit Mini

A working slice of a client subscription dashboard. Someone signs up to a monthly plan
through Stripe test mode, the system records the payment, and one page shows that person
their plan, status and renewal date — laid out for a phone first.

**Live:** https://orbit.ehnand.com — served from a machine in a living room in the
Philippines, published through a Cloudflare Tunnel. No cloud host.

FastAPI owns all state, Stripe and truth. Next.js is presentation only and can reach the
database through nothing but the API.

| | |
|---|---|
| **The report** — hours, gaps, and what I would do differently | [`docs/REPORT.md`](docs/REPORT.md) |
| **The contract** — layers, UX laws, the accessibility floor, definition of done | [`AGENTS.md`](AGENTS.md) |
| **The architecture** — the full tree for every surface, and why | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |

---

## Try it without signing up

The pricing page offers a one-click disposable demo account. It is capped at five; making
a sixth evicts the oldest. The walkthrough video is embedded on the same page.

---

## Run it locally

Docker with Compose. From the repository root:

```bash
cp .env.example .env     # set POSTGRES_PASSWORD, JWT_SECRET (32+ chars), Stripe keys
make dev                 # build, start, migrate
```

`make` on its own lists every target.

| | Development | Production |
|---|---|---|
| Web | http://localhost:7301 | 7311, behind the tunnel |
| API | http://localhost:7302 | 7312 |
| Postgres | 7303 | 7313 |
| pgAdmin | 7304 | 7314, **no tunnel route** |

Two stacks, two databases, two sets of containers. Working on development cannot disturb
what the public site serves. Every published port binds to `127.0.0.1`.

Not 3000/8000/5432 — all three were already taken on the machine this was built on.
Reasoning in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) section 7.

pgAdmin has no ingress rule in the tunnel config, which is what keeps a database admin UI
off the public internet. That is not a firewall decision; it is simply unroutable.

---

## Tests

```bash
make test        # 47 tests, no network, no Stripe keys required
```

The suite needs a running Postgres, which `make dev` provides. It creates a separate
`orbit_test` database, builds the schema **by running the Alembic migrations** — so every
run also proves the deploy path still works — and rolls back each test in a transaction.

It covers the four cases the brief names:

| | |
|---|---|
| Sign-up creates **exactly one** subscriber and returns a Checkout URL | `test_signup.py` |
| A valid webhook signature marks the subscriber active | `test_webhook.py` |
| An invalid signature is rejected **and writes nothing** | `test_webhook.py` |
| A replayed event leaves one row, unchanged | `test_webhook.py` |

Two of those cannot be produced by hand at any price. Stripe will never send a
badly-signed payload, and it cannot be told to redeliver on demand, so forging both is the
only way that code ever runs.

**Stripe is stubbed at a single point.** `app/services/stripe_client.py` is the only module
that imports `stripe`. Signature verification itself is *not* stubbed — it is the thing
under test.

`test_stripe_client.py` stubs one level lower still, at `stripe.Subscription.retrieve`,
returning real `StripeObject` instances. Two production 500s came from treating Stripe
objects as dictionaries, and a test that stubs with a plain dict cannot catch that.

---

## Layout

```
api/     FastAPI — controllers, services, repositories, models, schemas
web/     Next.js — presentation only
mobile/  Flutter package: the status card, plus a gallery of every state
media/   FFmpeg → Runpod pipeline (NOT BUILT — see the report)
infra/   compose for both stacks, and the tunnel config
```

The layer list in `AGENTS.md` section 3.3 is closed. A folder outside it is a bug, not a
judgement call.

---

## Not built

- **FFmpeg processing with a Runpod integration.** Not started. `media/` holds no working
  pipeline. This is the one scored item that is simply absent — see
  [`docs/REPORT.md`](docs/REPORT.md) section 5 for that and every other gap, including
  the ones you would otherwise have to find yourself.

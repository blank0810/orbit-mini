# Orbit Mini

Orbit Mini is a working slice of a client subscription dashboard, currently at the
scaffold stage. The intended flow is that a person signs up for a monthly plan
through Stripe test mode, the system records the payment, and one page shows that
person their plan and status. FastAPI owns all state; Next.js is presentation only.
The subscription flow is not built yet.

## Prerequisites

Docker with Docker Compose support. From the repository root, create your local
configuration:

```bash
cp .env.example .env
```

Set `POSTGRES_PASSWORD` and `PGADMIN_DEFAULT_PASSWORD` in `.env` before starting.
Keep `.env` local; it is gitignored.

## Run

From the repository root:

```bash
docker compose -f infra/docker-compose.yml up --build
```

## URLs

| Service | URL |
| --- | --- |
| Web | http://localhost:7301 |
| API | http://localhost:7302 |
| Liveness (no database check) | http://localhost:7302/api/health |
| Readiness (database `SELECT 1`) | http://localhost:7302/api/health/ready |
| pgAdmin (development tool) | http://localhost:7304 |


## Tests

```bash
cd api && uv run pytest
```

35 tests, no network and no Stripe keys. The suite needs a running Postgres, which
`docker compose` already provides; it creates and migrates a separate `orbit_test`
database so live data is never touched, and every test runs in a transaction that rolls
back.

It covers the four cases the brief requires:

| | |
|---|---|
| Sign-up creates **exactly one** subscriber and returns a Checkout URL | `test_signup.py` |
| A valid webhook signature marks the subscriber active | `test_webhook.py` |
| An invalid signature is rejected **and writes nothing** | `test_webhook.py` |
| A replayed event leaves one row, unchanged | `test_webhook.py` |

Two of those cannot be produced by hand at any price. Stripe will never send a
badly-signed payload, and it cannot be told to redeliver on demand, so forging both is the
only way that code ever runs.

Stripe is stubbed at a single point. `app/services/stripe_client.py` is the only module in
the codebase that imports `stripe`, which is what makes the suite offline and the
forged-signature test possible. Signature verification itself is **not** stubbed: it is the
thing under test.

## Development tools

pgAdmin is a development convenience for inspecting the database, bound to
`127.0.0.1`, and is not required to run the application.

## Ports

Host ports **7301** (web), **7302** (API), and **7303** (PostgreSQL) avoid
collisions with other projects using 3000, 8000, and 5432 on this machine.
They map to container ports 3000, 8000, and 5432 respectively. Every published
port binds explicitly to loopback (`127.0.0.1`), so access is local to this machine.

## Not built yet

- Subscriber model and its migration
- Accounts and login
- Stripe Checkout and the payment webhook
- Dashboard UI
- Test suite
- Cloudflare Tunnel
- Flutter status-card widget
- FFmpeg/Runpod media pipeline

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

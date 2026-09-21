# Orbit Mini

A working slice of a client subscription dashboard.

Someone signs up to a monthly plan through Stripe (test mode), the system records the
payment, and one page shows that person their plan and status, laid out for a phone.

| Layer | Technology |
|---|---|
| API and system of record | FastAPI, SQLAlchemy 2.0, Python 3.11+ |
| Database | PostgreSQL 16, one table |
| Payments | Stripe Checkout (test mode), webhook-driven |
| Dashboard | Next.js 16, React 19, TypeScript, Tailwind 4 |
| Mobile | Flutter component |
| Media | FFmpeg plus Runpod API |
| Delivery | Docker, docker compose, Cloudflare Tunnel |

## Status

Scaffolded. See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the build
sequence and [`AGENTS.md`](AGENTS.md) for the engineering contract.

## Running it

```bash
cp .env.example .env    # fill in Stripe test keys
docker compose -f infra/docker-compose.yml up --build
```

Detailed setup, the public URL, the decisions and their tradeoffs, and the list of what is
deliberately not built, all land here before delivery.

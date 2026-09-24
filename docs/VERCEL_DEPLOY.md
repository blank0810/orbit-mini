# Deploy Orbit Mini on Vercel

Production runs as **two Vercel projects** built from this one repository, with Postgres on
**Neon**. It moved there on 23 September 2026 from the self-hosted stack described at the end
of this file, because keeping that stack running on the build machine cost too much of its
resources.

## What runs where

| | Address | Vercel project root |
|---|---|---|
| Web (Next.js) | https://app.orbit.ehnand.com | `web/` |
| API (FastAPI) | https://orbit.ehnand.com | `api/` |
| Database | Neon Postgres | — |
| Stripe webhook | https://orbit.ehnand.com/api/webhooks/stripe | — |

The browser loads pages from `app.orbit.ehnand.com` and calls the API at
`orbit.ehnand.com/api` directly. The API host serves nothing outside `/api`.

The webhook URL is the one the tunnel served before the move, so the Stripe endpoint and its
signing secret carried over unchanged.

The Flutter package and the media pipeline are not deployed.

## Why the session cookie works across two hosts

The API sets the session as an httpOnly, `Secure`, `SameSite=Lax` cookie with no `Domain`
attribute, so it belongs to `orbit.ehnand.com` alone. `app.orbit.ehnand.com` and
`orbit.ehnand.com` share the registrable domain `ehnand.com`, which makes a credentialed
`fetch` from one to the other **same-site**: the browser attaches the cookie. The API's CORS
allowlist names the web origin and allows credentials.

That only holds while both hosts stay under `ehnand.com`. `vercel.app` is a public suffix, so
a web deployment on a `*.vercel.app` URL, which includes every preview deployment, is
cross-site to the API and is not on its CORS allowlist. Pages render there, but sign-in does
not. Test anything involving a session on the custom domain.

## Deploys

Both projects are connected to `blank0810/orbit-mini` on GitHub. A push to `main` deploys
production; other branches get preview deployments, which cannot sign in (see above).

Environment variable changes apply only to new deployments. Redeploy the affected project
after changing one.

## Environment variables

### API project (root `api/`)

Vercel finds the FastAPI `app` in `app/main.py`; `api/pyproject.toml` also names it under
`[tool.vercel]`. Dependencies install from `api/uv.lock`.

| Variable | Value |
|---|---|
| `DATABASE_URL` | Neon's **pooled** connection string. A plain `postgresql://` URL is fine: `Settings` switches it to the installed psycopg 3 driver. |
| `JWT_SECRET` | 32+ random characters (`openssl rand -hex 32`), never the development one |
| `ENVIRONMENT` | `production`, which turns on the cookie's `Secure` flag |
| `CORS_ORIGINS` | `https://app.orbit.ehnand.com` |
| `WEB_BASE_URL` | `https://app.orbit.ehnand.com`, where Stripe Checkout sends the customer back |
| `STRIPE_SECRET_KEY` | Stripe **test-mode** secret key |
| `STRIPE_WEBHOOK_SECRET` | Signing secret of the endpoint at `https://orbit.ehnand.com/api/webhooks/stripe` |
| `STRIPE_PRODUCT_ID_STARTER` | Starter product ID |
| `STRIPE_PRODUCT_ID_PRO` | Pro product ID |

The webhook handler acts on `checkout.session.completed` and
`customer.subscription.created`, `.updated` and `.deleted`; the Stripe endpoint needs those
four events.

### Web project (root `web/`)

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://orbit.ehnand.com` |

Next.js writes `NEXT_PUBLIC_*` values into the JavaScript bundle at build time, so changing
it takes a web redeploy, not just a restart. The web project holds no secret of any kind.

## Database

The API opens one connection per request and closes it (`NullPool` in
`app/db/session.py`). Vercel freezes function instances between requests, so a pool held
in-process would leak connections to Neon. Neon's pooled endpoint does the pooling instead.

**Deploys do not run migrations.** Apply them from a workstation, against Neon's **direct**
(unpooled) connection string, before merging code that needs them. Keep the URL in the
gitignored `.env.neon` at the repository root rather than in `api/.env`, where every local
`uv run` would pick it up and point at production:

```bash
# .env.neon holds DATABASE_URL=<direct Neon URL> and JWT_SECRET=<any 32+ characters>
cd api && (set -a && . ../.env.neon && uv run alembic upgrade head)
```

## DNS

Both hostnames are CNAME records in Cloudflare DNS pointing at the targets Vercel shows under
each project's **Domains** settings. They are **DNS only** (grey cloud), so Vercel terminates
TLS and issues the certificates. The apex `ehnand.com` and its other subdomains are not
involved.

## Verify

From the command line:

```bash
curl -s https://orbit.ehnand.com/api/health         # {"status":"ok"}
curl -s https://orbit.ehnand.com/api/health/ready   # {"status":"ready"}, so Neon is reachable
curl -s -o /dev/null -w '%{http_code}\n' https://app.orbit.ehnand.com/login   # 200
```

Then in a browser, on the custom domain: register, pay with `4242 4242 4242 4242`, confirm
Stripe shows the webhook delivery answered with 200, and check that the dashboard shows the
active plan and renewal date. Check it at 390px wide.

## The self-hosted setup this replaced

Until 23 September 2026, production was a local `docker compose` stack published through a
Cloudflare Tunnel, with web and API on one origin at `orbit.ehnand.com`.
`infra/docker-compose.prod.yml` and `infra/cloudflared/` are that deployment. They still work
and are kept as the record of that work, but nothing public routes to them any more: the
`orbit` DNS record now points at Vercel.

The Makefile's production targets (`deploy`, `verify`, `backup`, `reset-demo` and `prod-*`)
drive that local stack, not Vercel.

Page links from before the move, such as `https://orbit.ehnand.com/login`, now reach the API
host and return 404. The pages are at the same paths on `app.orbit.ehnand.com`.

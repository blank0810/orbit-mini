# AGENTS.md

Operating contract for any AI agent or human working in this repository.
Tool-agnostic on purpose: Claude Code, Codex, Cursor, or a person all follow this file.
`CLAUDE.md` adds Claude-Code-specific wiring only and never contradicts this document.

---

## 1. What this project is

**Orbit Mini** is a working slice of a client subscription dashboard.

A person signs up for a monthly plan through Stripe (test mode), the system records the
payment, and one page shows that person their plan and status, laid out properly on a phone.

It is a scored technical deliverable. Two things follow from that:

1. **It must run, publicly, on a real domain.** A repo that only works on localhost fails.
2. **It must not look like a default template.** Visual and interaction quality is part of
   the scoring surface, not decoration.

---

## 2. Stack and boundaries

| Layer | Technology | Lives in |
|---|---|---|
| API and system of record | **FastAPI** (Python 3.11+), SQLAlchemy 2.0 | `api/` |
| Database | **PostgreSQL 16**, one table | `api/` + compose |
| Payments | **Stripe Checkout**, test mode, webhook-driven | `api/` |
| Client dashboard | **Next.js 16** (App Router), React 19, TypeScript, Tailwind 4 | `web/` |
| Mobile component | **Flutter** | `mobile/` |
| Media pipeline | **FFmpeg** + **Runpod** API | `media/` |
| Delivery | Docker, docker compose, Cloudflare Tunnel | `infra/` |

### The boundary that matters most

**FastAPI owns all state, money, and truth. Next.js owns presentation.**

- No business logic in Next.js route handlers or server actions.
- No direct database access from `web/`. Ever. It talks to the API over HTTP.
- No Stripe secret key in `web/`. The publishable key is the only Stripe value the browser sees.
- If you are tempted to "just do it in Next.js because it is faster," that is the exact
  shortcut the brief is testing for. Do not take it.

---

## 3. Engineering principles

These are ranked. When two conflict, the higher one wins.

### 3.1 Correctness on money is non-negotiable

Payment code has rules that are not style preferences:

- **Webhook signatures are always verified.** `stripe.Webhook.construct_event` with the
  signing secret. An unverified webhook endpoint is an open write endpoint to your database.
- **Webhook delivery is at-least-once, so every handler is idempotent.** Store the Stripe
  event id and reject replays. Processing the same `checkout.session.completed` twice must
  leave the row identical.
- **Stripe is the source of truth for subscription status, not the browser.** The success
  redirect is a UI hint. Status changes only on a verified webhook.
- **Always return 2xx quickly to Stripe**, even on a duplicate. Non-2xx triggers retries.
- Amounts are integer minor units. Never floats.

### 3.2 YAGNI

Build what the brief asks for and nothing beyond it.

- One database table means **one** table. Not a users table plus a subscriptions table plus
  an audit table because "we might need it."
- No plan-tier abstraction layer for a single plan.
- No caching layer, no queue, no background worker until something actually blocks on one.
- No feature flags, no config knobs, no "we support both" branches. Every added choice is a
  decision someone has to make later, usually while debugging. Prefer one obvious path.
- If you cannot name the scored requirement a piece of code serves, delete it.

**The exception:** correctness, tests, and error handling are never "not needed yet."
YAGNI trims features, never rigor.

### 3.3 Layered, and only these layers

Boring, well-known tools over clever ones. Jakob's Law applies to codebases too: the next
reader expects it to work the way they already work. Here that means the layering a
Laravel or NestJS developer knows by reflex, because that is who maintains this next.

Every surface uses the same vocabulary, whatever language it is written in:

| Layer | Owns | Never does |
|---|---|---|
| **controller** | validate in, call one service, shape the response | business rules, queries |
| **service** | business logic, orchestration, external services | HTTP, SQL |
| **repository** | every query touching one table | business rules |
| **model** | the table declaration | queries, business rules |
| **schema** | request and response shapes | anything else |

`api/` is Python, `web/` is TypeScript, `mobile/` is Dart. The same words in all three, so
a reviewer opening any surface finds the same shape. Full tree: `docs/ARCHITECTURE.md`.

What still binds:

- **These layers and no others.** No `managers/`, no `helpers/`, no `utils/` dumping
  ground, no facade wrapping a facade. The table above is a closed list.
- **A thin file is the convention working. An invented layer is not.** A 25-line
  controller is correct. A `SubscriberServiceFactoryProvider` is not.
- **One module per external boundary.** Stripe, Postgres, Runpod and the API each get
  exactly one file that talks to them, and nothing else imports them. This is what makes
  the required tests writable: one thing to stub, not twelve.
- A comment that explains *why* beats a helper that hides *what*.

### 3.4 Readable beats short

Optimize for the person reading this under time pressure, which includes the reviewer
scoring it. Name things after what they mean in the domain (`subscriber`, `plan_status`),
not after their shape (`data`, `obj`, `result`).

### 3.5 Every change is deployable

`docker compose up` from a clean checkout plus a `.env` must produce a working system.
If a step lives only in your shell history, it is not delivered. Write it down in `README.md`.

---

## 4. UI/UX laws

Interface work is justified against these laws, not against taste. **Name the law in the
rationale.** If you cannot say which law a visual choice serves, it is pixel-pushing:
reconsider the interaction before touching the pixels.

| Law | What it demands here |
|---|---|
| **Hick's Law** | Every added choice slows the decision after it. Count the actions, links and fields competing on a screen. **One primary action per view.** The dashboard has exactly one: manage the subscription. Pricing shows one plan, so the choice is yes or no, not a comparison matrix. |
| **Fitts's Law** | Frequent and primary actions get bigger targets, placed near where the thumb already is. On mobile that is the lower half of the screen, not a 32px link in a header. Pad hit areas beyond the visible box. |
| **Jakob's Law** | Users expect it to behave like the SaaS dashboards they already use. Do not reinvent nav, status badges, billing pages or forms without a clear payoff. |
| **Miller's Law** | Chunk. Past roughly 7 items, a list or form needs grouping, sections or pagination. Group the dashboard into identity, plan, and billing-history regions. |
| **Tesler's Law** | Inherent complexity moves, it never vanishes. Absorb it in the system through defaults, inference and pre-fill rather than handing it to the user. The user should never type a plan id or a price id. |
| **Doherty Threshold** | Respond under 400ms or mask the wait with a skeleton or an optimistic update. A Stripe redirect and a webhook round trip both exceed it, so both need explicit pending states. Never a dead screen. |
| **Gestalt** (proximity, similarity, common region) | Spacing and grouping communicate relationships faster than borders and labels do. Reach for whitespace before reaching for a divider. |
| **Aesthetic-Usability Effect** | Polish buys trust, but it never substitutes for real usability. Ship the working status states before the gradient. |

### Accessibility floor, never traded away

**WCAG 2.2 AA.** Text contrast 4.5:1, UI and graphical contrast 3:1, visible focus indicator
on every interactive element, full keyboard operation, touch targets at least 24x24 CSS px
(aim for 44x44 on primary mobile actions).

Also apply Nielsen's 10 heuristics and Norman's affordances, signifiers, feedback and
constraints. In particular: **visibility of system status.** A subscription that is
`incomplete`, `active`, `past_due` or `canceled` must look obviously different at a glance,
and must never rely on colour alone to say so.

### Mobile is the primary target

The brief says "laid out properly on a phone." Design at 390px first, then let it grow.
Verify at 390x844 before calling any UI done. A desktop-first layout squeezed down is the
failure mode being tested for.

---

## 5. Testing

Tests are a scored deliverable. The brief names two specifically.

**Required, minimum:**
1. **Sign-up** creates exactly one subscriber row and returns a Stripe Checkout URL.
2. **Payment webhook** with a valid signature marks the subscriber active.
3. **Webhook with an invalid signature is rejected** with 400 and writes nothing.
4. **Webhook replay is idempotent**: same event twice leaves one row, unchanged.

Rules:
- `pytest` for the API. Stripe is stubbed at the boundary, never called live in tests.
- Tests run against a real Postgres in CI-or-compose, or a transactional fixture. Not mocks
  of the ORM.
- A test that cannot fail is not a test. Assert the invariant, not the happy path shape.
- Run the suite before claiming anything works. **Evidence before assertions, always.**

---

## 6. Security

- **Never commit secrets.** `.env` is gitignored. `.env.example` carries key names with
  empty values and is committed.
- Stripe **secret** key and **webhook signing secret** live only in the API environment.
- Validate and parse every inbound payload with Pydantic. No raw dict access on request bodies.
- Do not log full Stripe event bodies, emails, or any key material.
- CORS on the API is an explicit allowlist, never `*`.
- The public tunnel exposes a real service to the internet. Treat every endpoint as hostile-facing.

---

## 7. Repository layout

```
orbit-mini/
├── AGENTS.md              # this file, the contract
├── CLAUDE.md              # Claude Code specifics, points here
├── README.md              # how to run it, written for the reviewer
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── ARCHITECTURE.md    # the layer contract and the full tree
│   └── design-tokens.md   # scalesage.ai palette, type, the plan we sell
├── api/                   # FastAPI, layered: controllers/services/repositories/models
├── web/                   # Next.js dashboard
├── mobile/                # Flutter component
├── media/                 # FFmpeg + Runpod worker
└── infra/                 # docker-compose, cloudflared config, deploy notes
```

Keep the root clean. New top-level files need a reason.

---

## 8. Commands

```bash
# Full stack
docker compose -f infra/docker-compose.yml up --build

# API only  (7302: 8000 is taken by other projects on this machine)
cd api && uv run uvicorn app.main:app --reload --port 7302
cd api && uv run pytest -q

# Web only  (7301: 3000 is taken too)
cd web && pnpm dev --port 7301
cd web && pnpm lint && pnpm build

# Stripe webhooks during local dev
stripe listen --forward-to localhost:7302/api/webhooks/stripe

# Public tunnel
cloudflared tunnel --config infra/cloudflared/config.yml run
```

---

## 9. Git conventions

- Format: `type(scope): description`, under 72 characters.
- Types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`.
- Scopes here: `api`, `web`, `mobile`, `media`, `infra`, `docs`.
- Feature branches, then a PR into `main`. Never force-push `main`.
- Commit your own work only. Never revert, reformat or stage changes you did not make.
- Format with the project formatter before committing: `ruff format` in `api/`,
  `pnpm lint --fix` in `web/`, `dart format` in `mobile/`.

---

## 10. Definition of done

A task is done when all of these are true. Not four of five.

- [ ] It runs from a clean `docker compose up` with only `.env` supplied.
- [ ] Tests pass, and you ran them and saw the output.
- [ ] The UI was checked at 390px width and keyboard-navigated.
- [ ] No secret, key, or `.env` is staged.
- [ ] `README.md` reflects any new setup step.
- [ ] Anything beyond the brief is a **recorded** decision, not drift. The brief did not
      ask for accounts or a login; they are in anyway, by the operator's call, and section
      12 says why. Nothing else gets added without the same treatment.

---

## 11. Added beyond the brief, on purpose

The brief asks for no authentication. Orbit Mini has it anyway: first name, last name,
email, password, and a login.

**Why.** The role is maintaining a *client* dashboard. `GET /api/subscribers/{email}` on a
public domain hands any caller any customer's plan, status and billing date by guessing an
address. A reviewer scoring a payments deliverable tries that first. Real accounts close it
properly, and "shows *that person* their plan" becomes literally true rather than nearly true.

**What it costs.** Roughly two hours, and the scored core is what those hours came out of.
The report states this plainly: it was a deliberate addition, not a misread brief.

**What it must not cost.** R6 is one table. Password hashes are a column on `subscriber`.
A sessions table would be a second table, so the session is a **stateless signed JWT in an
httpOnly cookie**. No session storage, no second table, R6 intact.

---

## 12. Honesty rules

The deliverable includes a written report naming **hours spent and anything unfinished**.
That is graded. So:

- **Never claim something works that you have not run.** Run it, read the output, then claim it.
- **Unfinished is reported as unfinished.** A truthful gap costs far less than a claim that
  dies on the first question.
- Never fabricate or round up a number: hours, coverage, throughput, anything.
- If a requirement was cut, say which one and why, in one flat sentence. No apology, no
  hedging, no padding.

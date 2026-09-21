# Handover, session `career-operation-81` to `orbit-mini-e9`

**Written:** 2026-09-21
**Repo state at handover:** scaffolded, zero commits, clean. Nothing of yours to preserve.

> **Historical record, superseded in three places.** Kept as written rather than rewritten.
> Since this was handed over: ports are **7301 web / 7302 api / 7303 postgres**, because
> 3000/8000/5432 all collide with other projects on this machine. `AGENTS.md` section 3.3 is
> now a **layered contract** (controller / service / repository / model / schema), not
> flat-over-nested. And the brief itself was recovered to `docs/brief.md`, which confirmed
> the requirement table here is accurate and that Phase 7 is requested by name.
> Current truth: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/brief.md`.

---

## 1. Read these two first, in this order

1. **[`AGENTS.md`](../AGENTS.md)** is the engineering contract and it governs. Stack
   boundaries, YAGNI and KISS as ranked principles, the eight UX laws, the WCAG 2.2 AA
   floor, the four required tests, webhook rules, definition of done.
2. **[`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md)** is the build sequence: all 15
   scored items mapped to tiers, the data model, the API surface, eight phases each with a
   verification gate, and the risk table.

`CLAUDE.md` is thin and defers to `AGENTS.md`. `web/AGENTS.md` and `web/CLAUDE.md` are
one-line pointers that replaced the ones `create-next-app` generated.

---

## 2. The one thing that is still blocking

**The stated deadline is today, Monday 2026-09-21.** Cy is gating a Wednesday 23 September
start on it. The honest estimate is ~14 working hours: ~10.5 for the pass/fail core,
~3.5 for the Flutter component and the FFmpeg/Runpod pipeline.

That does not fit in what is left of today. The operator was asked to pick and **has not
answered yet**:

- **Option A:** ship the P0 core tonight, report Flutter and FFmpeg/Runpod as unfinished.
  The brief explicitly asks for an unfinished list, so this is a supported outcome.
- **Option B:** message Cy for Tuesday. Still clears a Wednesday start.

**Get this answered before starting Phase 1**, because it changes how much of P1 is worth
attempting. Do not assume Option A and quietly drop scope.

---

## 3. Decisions already settled, do not relitigate

Full reasoning in `IMPLEMENTATION_PLAN.md` section 1. Summary:

| Decision | Why |
|---|---|
| **FastAPI owns all state, Stripe and truth. Next.js is presentation only.** | The brief mandates FastAPI. Doing payment work in a Next.js route handler looks like it works while failing the scored requirement. This is the shortcut the exam is testing for. |
| **Cloudflare Tunnel, not Vercel.** | The brief says host locally and tunnel out, "we want to see the DevOps/Docker/sysadmin side directly." Vercel hides the Dockerfile and the compose work, which is the thing being scored. |
| **Stripe Checkout, hosted. No custom card form.** | Fastest path and the correct one. No card data touches the stack, so there is no PCI surface to defend in the report. |
| **One table means one table.** | `subscriber`. Idempotency via a `last_stripe_event_id` column, not a second events table. |
| **Postgres, not SQLite.** | Compose needs a service and infrastructure is being scored. Schema via a single Alembic migration so the deploy story is honest. |
| **Repo name `orbit-mini`.** | Operator-confirmed. Taken from Cy's own wording. No client name on a repo that may go public. |

---

## 4. Environment, already verified on this machine

Do not spend time rediscovering this. All present and working:

| Tool | Version |
|---|---|
| Node | v22.21.0 |
| pnpm | 10.25.0 |
| Python | 3.10.12 system, **use `uv` to pin 3.11+ for the API** |
| uv | 0.12.3 |
| Docker | 29.6.0 |
| cloudflared | 2026.6.1 |
| stripe CLI | installed at `/usr/bin/stripe` |
| Flutter / Dart | installed via snap |
| FFmpeg | 4.4.2 |
| codex | 0.154.0 |

**`ehnand.com` is already on Cloudflare with a live named tunnel** (`ssh.ehnand.com`,
credentials in `~/.cloudflared/`). So `orbit.ehnand.com` is configuration, not new
infrastructure. That is a real time saving in Phase 5.

⚠️ System Python is **3.10**. `uv` must pin 3.11+ for the API, do not build against 3.10.

---

## 5. What is on disk

```
orbit-mini/
├── AGENTS.md                      the contract, 247 lines
├── CLAUDE.md                      Claude-specific, defers to AGENTS.md
├── README.md                      reviewer-facing, still a stub
├── .gitignore                     .env, tunnel creds, py/node/flutter/media
├── docs/
│   ├── IMPLEMENTATION_PLAN.md     the build sequence, 275 lines
│   └── HANDOVER.md                this file
├── web/                           Next.js 16.3.5, React 19.2.8, TS, Tailwind 4,
│                                  App Router, src/, pnpm. `pnpm build` passes.
├── api/                           EMPTY
├── mobile/                        EMPTY
├── media/                         EMPTY
└── infra/cloudflared/             EMPTY
```

⚠️ **The empty directories are not tracked by git.** They exist on disk but will not survive
a clone until they contain a file. Do not be surprised if they vanish.

Branch is `main` (renamed from the `git init` default `master`). **No remote yet, zero
commits.** The operator is creating the GitHub repo. First commit is still unmade, so
`git add -A` is currently safe, but re-check before you run it.

---

## 6. Start here

**Phase 1, API core.** `IMPLEMENTATION_PLAN.md` section 4.

The gate on Phase 1 is the one that matters most: before any UI exists, run
`stripe listen --forward-to localhost:8000/api/webhooks/stripe`, complete a real test
checkout, and **read the row out of Postgres with your own eyes.** "Webhook never arrives"
is the failure that kills this on camera in Phase 8. Find it now, not in Phase 5.

Phase 2 (tests) is written alongside Phase 1, not after it.

---

## 7. Traps worth naming

- **Delete the Next.js boilerplate before styling anything.** The default page, the Vercel
  SVGs in `web/public/`, the default favicon. R9 is "looks like it belongs on scalesage.ai,
  not a default template", and a leaked Vercel logo in the demo video is a self-inflicted wound.
- **Confirm Runpod credentials in the first 15 minutes of Phase 7**, not two hours in. If
  they are unavailable, stop and report it blocked.
- **Test the tunnel from a phone on mobile data**, not from a second browser tab on the same
  machine. Those fail differently.
- **`flutter doctor` before Phase 6 starts.** Snap Flutter cold start can eat the budget.
- **Never run a live Stripe call in a test.** Test mode still means stub at the boundary.
- **Never log or print** a Stripe secret key, webhook signing secret, Runpod key, or tunnel
  credential, including while debugging.
- **Ports in play:** 3000 web, 8000 api, 5432 postgres. Check they are free before binding.

---

## 8. Concurrent sessions

I am `career-operation-81`. **I am done with this repo and will not touch it again**, so you
have it. If that changes I will message you first.

If you find changes you did not make, they are someone else's: do not stage, revert or
reformat them. Message the session that owns them.

---

## 9. Honesty rules carry into the deliverable

The brief requires a written report with **hours spent and anything unfinished**. That is
graded output, not a confession.

- Track hours per phase as you go. Reconstructing them at 2am produces a number that is
  not true.
- Never claim something works that you have not run. Run it, read the output, then claim it.
- A truthfully reported gap costs far less than a claim that dies on the reviewer's first
  question.

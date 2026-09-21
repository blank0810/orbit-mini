# CLAUDE.md

## Read AGENTS.md first

**[`AGENTS.md`](./AGENTS.md) is the operating contract for this repository and it governs.**
Stack boundaries, YAGNI, the layer contract, the UI/UX laws, the accessibility floor,
testing requirements, security rules, git conventions and the definition of done all live
there, because Codex and any other agent read the same file.

The layer contract in `AGENTS.md` section 3.3 is expanded, with the full tree for every
surface, in [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md). Read it before creating a
file in `api/`, `web/`, `mobile/` or `media/`: the layer list is closed, and a new folder
outside it is a bug, not a judgement call.

This file holds only what is specific to Claude Code. It never contradicts `AGENTS.md`.
If something here appears to conflict, `AGENTS.md` wins and this file is the bug.

---

## The one-line brief

A person signs up for a monthly plan through Stripe test mode, the system records the
payment, and one page shows that person their plan and status, laid out properly on a phone.
FastAPI behind it, one table, tests for sign-up and the payment webhook, a Dockerfile,
served publicly over a Cloudflare Tunnel. Plus a Flutter component and an FFmpeg-to-Runpod
pipeline to show infrastructure and integration range.

Full breakdown and sequencing: [`docs/IMPLEMENTATION_PLAN.md`](./docs/IMPLEMENTATION_PLAN.md).

---

## Working agreement

**Plan here, implement with Codex, review here.** When a task reaches the point of actually
writing or editing code, hand a self-contained instruction to Codex:

```bash
codex exec --sandbox workspace-write -c 'approval_policy="never"' "<full instruction>"
```

Do not pass `-m`. Let Codex pick its own model and effort. The prompt must be self-contained
(plan, exact paths, acceptance criteria, the conventions from `AGENTS.md`) because Codex does
not share this conversation. Codex leaves the work uncommitted; review the diff here against
`AGENTS.md` section 10 before committing.

Planning and review always stay on this side.

---

## Subagents

Use them for review and for parallel independent work, not to fan out the same task.

| Agent | Use for |
|---|---|
| `lead-engineer` | Architecture calls, the API and data-model shape, tradeoff decisions |
| `backend-engineer` | FastAPI routes, SQLAlchemy models, Stripe integration, webhook handling |
| `ui-ux-engineer` | The dashboard and pricing page, mobile layout, the UX laws in `AGENTS.md` section 4 |
| `qa-engineer` | The pytest suite, edge cases, pre-ship correctness review |
| `devops-engineer` | Dockerfile, compose, the Cloudflare Tunnel, the public domain |
| `security-engineer` | Adversarial review of the webhook and any money-touching diff |

Dispatch independent agents in a single message so they run concurrently.

---

## Skills

Resolve tooling at dispatch time from the injected skills listing. Do not hardcode a skill
name into a brief and expect compliance, and never install a skill mid-task: name the gap,
proceed with what exists, and say what that costs.

Likely relevant here: `superpowers:test-driven-development` for the webhook work,
`superpowers:systematic-debugging` when Stripe or the tunnel misbehaves, and the UI/UX
skills for `web/`. Arbitrate, do not assume.

---

## Guardrails specific to this repo

- **Never run a live Stripe call in a test.** Test mode still means stub at the boundary.
- **Never print or log a Stripe secret key, webhook signing secret, Runpod key, or tunnel
  credential**, including inside a debugging session.
- **Never commit `.env`**, `infra/cloudflared/*.json`, or any tunnel credential file.
- **Check the port is free before binding.** Ports in play: **7301 web, 7302 api,
  7303 postgres**, all bound to `127.0.0.1`. Not 3000/8000/5432 — every one of those is
  already claimed by another project on this machine. Reasoning in `docs/ARCHITECTURE.md`
  section 7.
- **Do not trigger browser dialogs** during Playwright or Chrome verification. Console logs
  and `read_console_messages` instead.
- **Do not add a dependency without saying why** in the same message. Every dependency is a
  choice someone maintains later.

---

## Verification before any completion claim

Before saying a piece of this works:

1. Run the command. Read the actual output.
2. For UI: load it, look at it at 390px wide, tab through it.
3. For the webhook: fire a real test event through `stripe trigger` or the tunnel and read
   the database row.

Evidence before assertions. A claim in the end-of-day report that does not survive the
reviewer's first question costs more than an honest gap.

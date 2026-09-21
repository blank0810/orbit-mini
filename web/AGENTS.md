# AGENTS.md (web)

This package has no separate contract. The repository contract is [`../AGENTS.md`](../AGENTS.md).

What applies most directly here: `web/` is presentation only. No database access, no Stripe
secret, no business logic. It calls the FastAPI service over HTTP. UI work is justified
against the UX laws in `../AGENTS.md` section 4, and mobile at 390px is the primary target.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

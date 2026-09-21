# AGENTS.md (web)

This package has no separate contract. The repository contract is [`../AGENTS.md`](../AGENTS.md).

What applies most directly here: `web/` is presentation only. No database access, no Stripe
secret, no business logic. It calls the FastAPI service over HTTP. UI work is justified
against the UX laws in `../AGENTS.md` section 4, and mobile at 390px is the primary target.

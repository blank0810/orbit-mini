# Orbit Mini
#
# Two separate stacks. `orbit-dev` is where changes are built and checked; `orbit-prod` is
# what orbit.ehnand.com serves. They have their own containers, networks and DATABASES, so
# working on one cannot disturb the other.
#
#   dev   web :7301  api :7302  db :7303  pgadmin :7304
#   prod  web :7311  api :7312  db :7313  pgadmin :7314   + the Cloudflare Tunnel

DEV  := docker compose -f infra/docker-compose.yml
PROD := docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml
PUBLIC := https://orbit.ehnand.com

.DEFAULT_GOAL := help
.PHONY: help test lint dev dev-down dev-logs dev-migrate dev-seed \
        deploy prod-up prod-migrate prod-logs prod-down verify backup reset-demo

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# --- checks -----------------------------------------------------------------------

test: ## Run the API test suite (no network, no Stripe keys)
	cd api && uv run pytest

lint: ## Format and lint both sides
	cd api && uv run ruff format . && uv run ruff check .
	cd web && pnpm lint

# --- development ------------------------------------------------------------------

dev: ## Build and start the development stack
	$(DEV) up -d --build
	@$(MAKE) --no-print-directory dev-migrate

dev-migrate: ## Apply migrations to the development database
	$(DEV) exec -T api alembic upgrade head

dev-seed: ## Seed the advertised demo account into development
	$(DEV) exec -T api python -m app.seed_demo

dev-logs: ## Tail development logs
	$(DEV) logs -f --tail=100

dev-down: ## Stop development. Data survives; add -v yourself to wipe it.
	$(DEV) down

# --- production -------------------------------------------------------------------

deploy: test prod-up prod-migrate verify ## Test, build, start, migrate, then check the PUBLIC url
	@echo ""
	@echo "  deployed. $(PUBLIC)"

prod-up: ## Build and start production (does NOT touch the database)
	$(PROD) up -d --build

prod-migrate: ## Apply migrations to the production database
	$(PROD) exec -T api alembic upgrade head

prod-logs: ## Tail production logs
	$(PROD) logs -f --tail=100

prod-down: ## Stop production. Never pass -v here unless you mean to delete every subscriber.
	$(PROD) down

verify: ## Ask the PUBLIC url, not localhost. Only this proves a visitor sees the change.
	@printf '  health   %s\n' "$$(curl -s --max-time 15 $(PUBLIC)/api/health)"
	@printf '  ready    %s\n' "$$(curl -s --max-time 15 $(PUBLIC)/api/health/ready)"
	@printf '  pricing  HTTP %s\n' "$$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 $(PUBLIC)/)"
	@printf '  login    HTTP %s\n' "$$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 $(PUBLIC)/login)"

backup: ## Dump the production database to backups/ before anything risky
	@mkdir -p backups
	@$(PROD) exec -T db pg_dump -U orbit -d orbit --clean --if-exists \
		> backups/prod-$$(date +%Y%m%d-%H%M%S).sql
	@ls -1t backups | head -1 | sed 's/^/  wrote backups\//'

reset-demo: ## Wipe demo data in production and re-seed the advertised account
	$(PROD) exec -T api python -m app.reset_demo --yes

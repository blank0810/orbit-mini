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
        flutter-test flutter-demo flutter-stop \
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

# --- the Flutter component -------------------------------------------------------

FLUTTER_PKG := mobile/orbit_status_card
FLUTTER_PORT := 7390

flutter-test: ## Run the Flutter package tests (no server needed)
	cd $(FLUTTER_PKG) && flutter test

flutter-demo: ## Build and serve the Flutter card against the DEV api, then open it
	@echo "  the demo calls the dev API on 7302, so bring it up first if it is not running"
	cd $(FLUTTER_PKG)/example && flutter build web --release \
		--dart-define=ORBIT_API_BASE_URL=http://localhost:7302
	@# Flutter web ships a service worker that will happily serve a stale bundle after a
	@# rebuild. Deleting it here saves the "my change did nothing" hour.
	@rm -f $(FLUTTER_PKG)/example/build/web/flutter_service_worker.js
	@pid=$$(ss -ltnpH 2>/dev/null | grep ':$(FLUTTER_PORT) ' | grep -oP 'pid=\K[0-9]+' | head -1); \
		[ -n "$$pid" ] && kill $$pid 2>/dev/null || true
	@cd $(FLUTTER_PKG)/example/build/web && nohup python3 -m http.server $(FLUTTER_PORT) --bind 127.0.0.1 >/tmp/flutter-demo.log 2>&1 &
	@sleep 2
	@echo ""
	@echo "  http://localhost:$(FLUTTER_PORT)"
	@echo ""
	@echo "  Use localhost, NOT 127.0.0.1. They are different origins to CORS and only"
	@echo "  localhost is in the dev allowlist."

flutter-stop: ## Stop the Flutter demo server
	@pid=$$(ss -ltnpH 2>/dev/null | grep ':$(FLUTTER_PORT) ' | grep -oP 'pid=\K[0-9]+' | head -1); \
		if [ -n "$$pid" ]; then kill $$pid && echo "  stopped"; else echo "  not running"; fi

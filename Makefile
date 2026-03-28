# EcoSignal — Development Makefile
# Usage: make <target> [s=service-name]

COMPOSE = docker compose

.PHONY: up down logs health db-migrate restart clean ps

## Start all services (build + detach)
up:
	$(COMPOSE) up --build -d

## Stop all services
down:
	$(COMPOSE) down

## Tail logs (all services, or pass s=<name>)
logs:
ifdef s
	$(COMPOSE) logs -f $(s)
else
	$(COMPOSE) logs -f
endif

## Check health of all running services
health:
	@echo "=== EcoSignal Health Check ==="
	@curl -sf http://localhost:8000/health && echo " ✓ api-gateway"    || echo " ✗ api-gateway"
	@$(COMPOSE) exec -T user-profile      python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" 2>/dev/null && echo " ✓ user-profile"      || echo " ✗ user-profile"
	@$(COMPOSE) exec -T footprint-engine   python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" 2>/dev/null && echo " ✓ footprint-engine"  || echo " ✗ footprint-engine"
	@$(COMPOSE) exec -T env-data           python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" 2>/dev/null && echo " ✓ env-data"          || echo " ✗ env-data"
	@$(COMPOSE) exec -T ai-narrative       python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health')" 2>/dev/null && echo " ✓ ai-narrative"      || echo " ✗ ai-narrative"
	@$(COMPOSE) exec -T postgres           pg_isready -U ecosignal > /dev/null 2>&1 && echo " ✓ postgres"       || echo " ✗ postgres"
	@$(COMPOSE) exec -T redis              redis-cli ping > /dev/null 2>&1 && echo " ✓ redis"                  || echo " ✗ redis"

## Run Alembic migrations (user-profile)
db-migrate:
	$(COMPOSE) exec user-profile alembic upgrade head

## Restart a specific service (pass s=<name>)
restart:
ifdef s
	$(COMPOSE) restart $(s)
else
	@echo "Usage: make restart s=<service-name>"
endif

## Tear down everything including volumes (DESTRUCTIVE)
clean:
	$(COMPOSE) down -v --remove-orphans

## Show running containers
ps:
	$(COMPOSE) ps

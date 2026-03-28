# EcoSignal — Development Makefile

.PHONY: up down logs logs-service health db-migrate restart clean ps demo-trigger shell narrative-test

## Start all services (build + detach)
up:
	docker compose up --build -d

## Stop all services
down:
	docker compose down

## Tail logs (all services)
logs:
	docker compose logs -f

## Tail logs for a specific service
logs-service:
	@read -p "Service name: " svc; docker compose logs -f $$svc

## Check health of all service endpoints
health:
	@echo "Checking all service health endpoints..."
	@for port in 8000 8001 8002 8003 8004 8005 8006 8007; do \
		echo -n "Port $$port: "; \
		curl -sf http://localhost:$$port/health | python3 -m json.tool \
		|| echo "UNHEALTHY"; \
	done

## Run Alembic migrations (user-profile)
db-migrate:
	docker compose exec user-profile alembic upgrade head

## Restart a specific service
restart:
	@read -p "Service name: " svc; docker compose restart $$svc

## Tear down everything including volumes (DESTRUCTIVE)
clean:
	docker compose down -v --remove-orphans

## Show running containers
ps:
	docker compose ps

## Trigger env-data prefetch job via scheduler
demo-trigger:
	@echo "Triggering env-data prefetch job..."
	curl -sf http://localhost:8007/health/trigger/prefetch_active_zips \
		| python3 -m json.tool

## Open a shell in a service container
shell:
	@read -p "Service name: " svc; \
	docker compose exec $$svc /bin/bash

## End-to-end narrative test (register → onboard → get narrative)
narrative-test:
	@echo "Testing full narrative pipeline for ZIP 00100 (Roma)..."
	@echo "1. Register user..."
	@TOKEN=$$(curl -sf -X POST http://localhost:8000/api/v1/auth/register \
		-H "Content-Type: application/json" \
		-d '{"email":"demo@ecosignal.it","password":"demo1234","display_name":"Demo"}' \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"); \
	echo "Token: $$TOKEN"; \
	echo "2. Onboarding..."; \
	curl -sf -X POST http://localhost:8000/api/v1/onboarding \
		-H "Authorization: Bearer $$TOKEN" \
		-H "Content-Type: application/json" \
		-d '{"zip_code":"00100","transport_mode":"car","diet_type":"meat_weekly","home_type":"apartment","home_size_sqm":70}'; \
	echo "3. Get narrative..."; \
	curl -sf http://localhost:8000/api/v1/narrative \
		-H "Authorization: Bearer $$TOKEN" | python3 -m json.tool

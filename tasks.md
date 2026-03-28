Task list — EcoSignal Python backend
Each task maps to one module, is independently testable, and wires into the system via Docker Compose.

api-gateway — FastAPI entry point
TASK-01 [ARCH] Define OpenAPI contract: all endpoints, request/response schemas, error codes
TASK-02 [DEV]  Scaffold FastAPI app with versioned router (/api/v1/*)
TASK-03 [DEV]  Implement JWT auth middleware (issue + validate tokens)
TASK-04 [DEV]  Add rate limiting middleware (slowapi or custom Redis-backed)
TASK-05 [DEV]  Write integration tests: auth flow, 401/403 edge cases, rate limit behavior

user-profile — onboarding & habits
TASK-06 [ARCH] Design User and HabitProfile Pydantic schemas + Postgres table migrations
TASK-07 [DEV]  POST /onboarding endpoint: accept zip, transport, diet → persist profile
TASK-08 [DEV]  GET/PATCH /profile endpoint: retrieve and update habits
TASK-09 [DEV]  Unit tests: schema validation, missing fields, invalid ZIP codes
TASK-10 [DEV]  Pytest fixtures with in-memory SQLite for isolation (no Postgres dependency)

footprint-engine — CO₂ calculation
TASK-11 [ARCH] Research and encode ISPRA emission factors per category (transport, food, home)
TASK-12 [DEV]  Pure function: calculate_weekly_footprint(profile: HabitProfile) -> FootprintResult
TASK-13 [DEV]  Endpoint: POST /footprint/calculate → returns kg CO₂ breakdown by category
TASK-14 [DEV]  Endpoint: GET /footprint/history/{user_id} → weekly trend from Postgres
TASK-15 [DEV]  Unit tests: parametrized with known input/output pairs, zero dependencies

env-data — external environmental data
TASK-16 [ARCH] Map Italian ZIP codes to ARPA region + OpenAQ station IDs
TASK-17 [DEV]  Adapter: fetch_air_quality(zip: str) → AirQualityReading (OpenAQ v3 API)
TASK-18 [DEV]  Adapter: fetch_climate_anomaly(zip: str) → ClimateContext (Copernicus / ISPRA)
TASK-19 [DEV]  Redis caching layer: TTL=1h per ZIP, fallback to last known value on timeout
TASK-20 [DEV]  Unit tests: mock HTTP responses with pytest-httpx, test cache hit/miss logic
TASK-21 [DEV]  Contract tests: assert response schemas match expected structure from real APIs

ai-narrative — Claude API layer
TASK-22 [ARCH] Design prompt template: inputs (footprint, env context, user habits) → narrative output schema
TASK-23 [DEV]  Service: generate_narrative(footprint, env_data, profile) → NarrativeResponse
TASK-24 [DEV]  Structured output parsing: enforce JSON mode, validate with Pydantic
TASK-25 [DEV]  Retry + fallback logic: exponential backoff on API errors, static fallback copy
TASK-26 [DEV]  Unit tests: mock Anthropic SDK, test prompt assembly and output parsing in isolation
TASK-27 [DEV]  Prompt regression tests: snapshot test on narrative output given fixed inputs

actions-engine — suggestions & impact scoring
TASK-28 [ARCH] Define action catalogue schema: id, category, effort_score, co2_saving_kg_week
TASK-29 [DEV]  Service: rank_actions(profile, footprint) → list[ActionSuggestion] top 3
TASK-30 [DEV]  Endpoint: GET /actions/{user_id} → returns ranked suggestions
TASK-31 [DEV]  Endpoint: POST /actions/{user_id}/complete → marks action done, updates streak
TASK-32 [DEV]  Unit tests: ranking logic, edge cases (all actions already completed, new user)

community — streaks, challenges, CAP aggregation
TASK-33 [ARCH] Design anonymized aggregation model: footprint avg per CAP without PII leakage
TASK-34 [DEV]  Service: get_neighborhood_stats(zip: str) → NeighborhoodStats (avg, rank, count)
TASK-35 [DEV]  Endpoint: GET /community/{zip}/stats
TASK-36 [DEV]  Endpoint: POST /community/challenge/join → enroll user in weekly challenge
TASK-37 [DEV]  Streak logic: compute_streak(user_id) → current streak days, last action timestamp
TASK-38 [DEV]  Unit tests: aggregation math, streak edge cases (gap in days, timezone handling)

scheduler — background jobs
TASK-39 [ARCH] Define job schedule: weekly footprint refresh, daily env-data prefetch per active ZIP
TASK-40 [DEV]  APScheduler setup inside dedicated container
TASK-41 [DEV]  Job: refresh_env_cache() — prefetch top 20 most active ZIPs every morning
TASK-42 [DEV]  Job: send_weekly_digest() — trigger ai-narrative for all active users
TASK-43 [DEV]  Unit tests: mock scheduler clock, assert jobs fire at correct intervals

Infrastructure & integration
TASK-44 [ARCH] Write docker-compose.yml: all 6 services + postgres + redis, health checks, env vars
TASK-45 [ARCH] Define shared .env.example with all required secrets (ANTHROPIC_API_KEY, DB_URL, etc.)
TASK-46 [DEV]  Alembic migrations: initial schema for users, footprints, actions, streaks
TASK-47 [DEV]  pytest-docker integration test suite: spin up compose stack, run E2E happy path
TASK-48 [DEV]  GitHub Actions CI: lint (ruff), type check (mypy), unit tests per module, integration test

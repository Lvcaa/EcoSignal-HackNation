# EcoSignal — AI Agent System Prompt

## Project overview
You are an AI agent working on EcoSignal ("Il Gemello Verde"), a Python backend
for a civic-tech web app that connects Italian citizens' daily habits to real
local environmental data. The system generates a personalized "climate narrative"
and actionable suggestions to reduce individual carbon footprint.

This project was built for the EcoSignal hackathon challenge proposed by Engineering S.p.A.
The prize is €2,500 in Amazon vouchers. The judges will evaluate:
- Technical quality and modularity
- Use of open environmental data
- AI integration with measurable impact
- Accessibility for non-technical Italian users

---

## Architecture principles — NON-NEGOTIABLE

1. **One module = one responsibility.** Every service is a standalone Python package
   with its own Dockerfile, its own requirements.txt, and its own pytest suite.
   A module must be fully testable with `pytest` and zero Docker dependencies.

2. **Contracts first.** No implementation starts before its Pydantic schemas and
   OpenAPI endpoint contracts are defined. The AI Architect defines contracts;
   the AI Developer implements against them.

3. **No shared state between modules except via HTTP or Redis.**
   Modules do not import from each other. They communicate only through
   internal HTTP calls (using httpx) or via shared Redis keys with documented TTLs.

4. **All secrets via environment variables.** No hardcoded credentials anywhere.
   Every secret is declared in `.env.example` with a description.

5. **Tests are first-class citizens.** Every function with business logic has a
   unit test. Every external API call is mocked in tests using pytest-httpx or
   unittest.mock. Coverage target: 80% per module minimum.

---

## System topology

The backend is composed of 6 Python microservices + 2 infra containers,
all orchestrated via Docker Compose on a single internal network.

Services:
- api-gateway      → FastAPI, JWT auth, rate limiting, routes to all services
- user-profile     → onboarding, habit storage (Postgres via SQLAlchemy)
- footprint-engine → CO₂ calculation using ISPRA emission factors (pure functions)
- env-data         → OpenAQ + ARPA + Copernicus adapters, Redis-cached by ZIP
- ai-narrative     → Claude API (claude-sonnet-4-20250514) prompt engine, structured output
- actions-engine   → action catalogue, impact ranking, streak tracking
- community        → anonymized CAP-level aggregation, weekly challenges
- scheduler        → APScheduler container for background jobs (daily + weekly)

Infra:
- postgres:16      → persistent storage (users, footprints, actions, streaks)
- redis:7          → cache layer (env data TTL=1h, sessions, rate limiting)

---

## Tech stack

- Python 3.12
- FastAPI + uvicorn (all services)
- SQLAlchemy 2.0 + Alembic (user-profile, footprint-engine, community)
- Pydantic v2 (all schemas and validation)
- httpx (async HTTP client for inter-service calls and external APIs)
- anthropic SDK (ai-narrative only)
- APScheduler (scheduler only)
- pytest + pytest-asyncio + pytest-httpx (all modules)
- ruff (linting) + mypy (type checking)
- Docker + Docker Compose v2

---

## Module structure (replicate for every service)
module-name/
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py          # FastAPI app instance + router registration
│   ├── config.py        # pydantic-settings BaseSettings
│   ├── models.py        # SQLAlchemy ORM models (if DB needed)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── service.py       # Pure business logic (no HTTP, no DB calls)
│   ├── repository.py    # DB access layer (if DB needed)
│   └── router.py        # FastAPI router, thin controllers only
└── tests/
├── conftest.py      # fixtures, test DB, mocked clients
├── test_service.py  # unit tests for service.py (pure, fast)
└── test_router.py   # integration tests for HTTP layer

---

## Data contracts (core schemas)

### HabitProfile
```python
class HabitProfile(BaseModel):
    user_id: UUID
    zip_code: str                          # Italian CAP (5 digits)
    transport_mode: TransportMode          # car | transit | bike | walk | mixed
    diet_type: DietType                    # meat_daily | meat_weekly | vegetarian | vegan
    home_type: HomeType                    # apartment | house
    home_size_sqm: int
    created_at: datetime
    updated_at: datetime
```

### FootprintResult
```python
class FootprintResult(BaseModel):
    user_id: UUID
    week_start: date
    total_kg_co2: float
    breakdown: dict[str, float]            # {"transport": 12.4, "food": 8.1, "home": 6.2}
    vs_national_avg_pct: float             # e.g. -0.12 means 12% below average
```

### AirQualityReading
```python
class AirQualityReading(BaseModel):
    zip_code: str
    station_id: str
    pm25: float | None
    pm10: float | None
    o3: float | None
    aqi_label: Literal["good", "moderate", "unhealthy", "hazardous"]
    fetched_at: datetime
    source: Literal["openaq", "arpa", "fallback"]
```

### NarrativeResponse
```python
class NarrativeResponse(BaseModel):
    user_id: UUID
    headline: str                          # 1 sentence, human tone, max 120 chars
    body: str                              # 2-3 sentences connecting habits to local data
    local_context: str                     # 1 sentence about today's local env conditions
    source_note: str                       # e.g. "Based on ISPRA 2024 · OpenAQ today"
    generated_at: datetime
```

### ActionSuggestion
```python
class ActionSuggestion(BaseModel):
    action_id: str
    title: str
    description: str
    category: Literal["transport", "food", "home", "community"]
    co2_saving_kg_week: float
    effort: Literal["easy", "medium", "hard"]
    completed: bool
```

---

## External APIs

| API | Base URL | Auth | Used by |
|-----|----------|------|---------|
| OpenAQ v3 | https://api.openaq.org/v3 | API key header | env-data |
| Copernicus CDS | https://cds.climate.copernicus.eu/api | key + UID | env-data |
| ISPRA open data | https://dati.isprambiente.it/api | none (public) | footprint-engine |
| Anthropic Claude | https://api.anthropic.com/v1 | Bearer token | ai-narrative |

All external calls must be wrapped in try/except with logged errors and
graceful fallback values. Never let an external API failure crash a user request.

---

## Claude API usage (ai-narrative module only)

Model: claude-sonnet-4-20250514
Max tokens: 1000
Temperature: default (do not override)

System prompt template for narrative generation:
You are EcoSignal's climate narrative engine. Your job is to write a short,
warm, non-alarmist message in Italian that connects a user's weekly habits
to real local environmental data. Be human, specific, and end with one
encouraging sentence. Never use technical jargon. Never blame the user.
Always ground the narrative in the actual numbers provided.
Respond ONLY with valid JSON matching this schema:
{"headline": "...", "body": "...", "local_context": "...", "source_note": "..."}

User message template:
User profile: {transport_mode}, {diet_type}, zip {zip_code}
Weekly footprint: {total_kg_co2} kg CO₂ ({vs_avg}% vs national average)
Breakdown: transport {transport_kg} kg, food {food_kg} kg, home {home_kg} kg
Local air quality today: PM2.5 {pm25} µg/m³ ({aqi_label})
Local climate context: {climate_context}

---

## Docker Compose conventions

- Every service exposes one internal port only (no host port mapping except api-gateway:8000)
- Health checks required on all services: GET /health → {"status": "ok"}
- Service startup order: postgres → redis → user-profile, footprint-engine, env-data → api-gateway, ai-narrative, actions-engine, community → scheduler
- All services share one network: ecosignal-net
- Volume: postgres_data persists across restarts

---

## Git conventions

- Branch per module: feature/module-name
- Commit format: [module-name] short description
- Every PR must include: implementation + tests + updated README for that module
- No PR is merged without green CI (ruff + mypy + pytest)

---

## What you must NEVER do

- Import from another service's Python package (use HTTP only)
- Hardcode any API key, password, or secret
- Write a function longer than 40 lines without splitting it
- Skip the /health endpoint on any service
- Let an external API error surface as a 500 to the user
- Use sync SQLAlchemy (always async with asyncpg)
- Generate narrative text outside the ai-narrative module

# EcoSignal Backend

Truck telemetry ingestion service for the EcoSignal waste-management platform.
Receives truck state updates and stores every version in PostgreSQL.

---

## Folder structure

```
van_management/
  app/
    api/v1/trucks.py      # Route handlers
    core/
      config.py            # Settings from env vars
      database.py          # SQLAlchemy engine & session
      logging.py           # Logging setup
    models/truck_state.py  # ORM model
    schemas/
      truck.py             # Pydantic request/response schemas
      common.py            # Shared response envelope
    repositories/
      truck_repository.py  # DB access layer
    services/
      truck_service.py     # Business logic
    main.py                # FastAPI app entrypoint
  tests/
    conftest.py            # Fixtures (SQLite in-memory)
    test_health.py
    test_trucks.py
  alembic/                 # Database migrations
  scripts/run_dev.sh       # Dev runner
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
  alembic.ini
```

---

## Quick start (Docker)

```bash
cd van_management
cp .env.example .env
docker compose up -d --build
docker compose exec van_management alembic upgrade head
```

The API will be available at `http://localhost:8000`.
The current public ngrok endpoint is
`https://dayana-nonfulminating-novella.ngrok-free.dev`.
When calling the public ngrok URL from scripts or API clients, include
`ngrok-skip-browser-warning: true`.
Swagger docs at `http://localhost:8000/docs`.
Public Swagger docs at
`https://dayana-nonfulminating-novella.ngrok-free.dev/docs`.
PostgreSQL stays internal to Docker Compose by default, which avoids conflicts
with any local Postgres already using port `5432`.

Full endpoint-by-endpoint integration docs are available in
`API_REFERENCE.md`.

### Run migrations inside Docker

```bash
docker compose up -d
docker compose exec van_management alembic upgrade head
```

The `van_management` service must be running before `docker compose exec ...` works.
Compose now overrides `DATABASE_URL` inside the container to use the internal
PostgreSQL host `db`, so your local `.env` can still keep `localhost` for
non-Docker development.

---

## Local development (without Docker)

Prerequisites: Python 3.12+, PostgreSQL running on localhost:5432.

```bash
cd van_management
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edit DATABASE_URL if needed
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

---

## Environment variables

| Variable       | Default                                              | Description              |
|----------------|------------------------------------------------------|--------------------------|
| `APP_NAME`     | `EcoSignal Backend`                                  | Service display name     |
| `APP_VERSION`  | `0.1.0`                                              | Reported version         |
| `DEBUG`        | `false`                                              | Debug mode               |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/ecosignal` | PostgreSQL connection |

---

## Migration commands

```bash
# Apply all migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# Generate a new migration after model changes
alembic revision --autogenerate -m "description"
```

---

## Running tests

Tests use an in-memory SQLite database, no PostgreSQL required.

```bash
cd van_management
pytest -v
```

---

## API contract

### `GET /health`

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/health \
  -H "ngrok-skip-browser-warning: true"
```

Response:
```json
{
  "success": true,
  "message": "OK",
  "data": null
}
```

### `GET /version`

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/version \
  -H "ngrok-skip-browser-warning: true"
```

Response:
```json
{
  "success": true,
  "message": "Service info",
  "data": {
    "name": "EcoSignal Backend",
    "version": "0.1.0"
  }
}
```

### `POST /api/v1/trucks/update`

Submit a truck state update. Every call creates a new versioned row.

```bash
curl -X POST https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/update \
  -H "ngrok-skip-browser-warning: true" \
  -H "Content-Type: application/json" \
  -d '{
    "truck_id": "TRUCK_001",
    "waste_type": "organic",
    "current_position": {
      "latitude": 45.4642,
      "longitude": 9.1900,
      "timestamp": "2026-03-28T10:15:00Z"
    }
  }'
```

**Payload fields:**

| Field                          | Type   | Required | Notes                                          |
|--------------------------------|--------|----------|-------------------------------------------------|
| `truck_id`                     | string | yes      | 1-64 characters                                 |
| `waste_type`                   | string | yes      | One of: `organic`, `paper`, `plastic`, `glass`, `mixed` |
| `current_position.latitude`    | float  | yes      | -90 to 90                                       |
| `current_position.longitude`   | float  | yes      | -180 to 180                                     |
| `current_position.timestamp`   | string | yes      | ISO 8601, e.g. `2026-03-28T10:15:00Z`           |

**Success response (201):**
```json
{
  "success": true,
  "message": "Truck TRUCK_001 updated to version 1",
  "data": {
    "id": 1,
    "truck_id": "TRUCK_001",
    "waste_type": "organic",
    "latitude": 45.4642,
    "longitude": 9.19,
    "position_timestamp": "2026-03-28T10:15:00Z",
    "version": 1,
    "created_at": "2026-03-28T12:00:00Z"
  }
}
```

**Validation error (422):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "waste_type"],
      "msg": "Input should be 'organic', 'paper', 'plastic', 'glass' or 'mixed'"
    }
  ]
}
```

### `GET /api/v1/trucks/{truck_id}/latest`

Retrieve the latest known state for a truck. This is the recommended endpoint
for clients that poll frequently.

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/TRUCK_001/latest \
  -H "ngrok-skip-browser-warning: true"
```

### `GET /api/v1/trucks/{truck_id}/history`

Retrieve full version history for a truck, newest first.

```bash
curl "https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/TRUCK_001/history?page=1&page_size=50" \
  -H "ngrok-skip-browser-warning: true"
```

**Query parameters:**

| Param       | Default | Range   |
|-------------|---------|---------|
| `page`      | 1       | >= 1    |
| `page_size` | 50      | 1 - 200 |

**Success response (200):**
```json
{
  "success": true,
  "message": "Found 2 record(s) for truck 'TRUCK_001'",
  "data": {
    "truck_id": "TRUCK_001",
    "total": 2,
    "page": 1,
    "page_size": 50,
    "records": [
      {
        "id": 2,
        "truck_id": "TRUCK_001",
        "waste_type": "organic",
        "latitude": 45.4700,
        "longitude": 9.2000,
        "position_timestamp": "2026-03-28T10:20:00Z",
        "version": 2,
        "created_at": "2026-03-28T12:05:00Z"
      },
      {
        "id": 1,
        "truck_id": "TRUCK_001",
        "waste_type": "organic",
        "latitude": 45.4642,
        "longitude": 9.1900,
        "position_timestamp": "2026-03-28T10:15:00Z",
        "version": 1,
        "created_at": "2026-03-28T12:00:00Z"
      }
    ]
  }
}
```

**Not found (404):**
```json
{
  "detail": "No history found for truck 'UNKNOWN'"
}
```

---

## Design notes

### Why single-table versioning?

The `truck_state_versions` table stores every update as a new row, keyed by `(truck_id, version)`.

- Simple to query: latest state = `MAX(version)`, full history = `SELECT * WHERE truck_id = ?`
- No UPDATE/DELETE needed: all writes are INSERTs
- Append-only design is safe for concurrent writers (e.g. multiple simulator instances)
- Easy to reason about for teammates integrating against this API

A two-table design (trucks + state_history) adds complexity with no benefit at this scope.

---

## Future TODOs

- [ ] Authentication / API key middleware
- [ ] Real route entities (route_id, waypoints, ETA)
- [ ] WebSocket endpoint for live truck position streaming
- [ ] Kafka / event-streaming ingestion for high-throughput scenarios
- [ ] Map integration helpers (tile URLs, geofencing)
- [ ] Restrict CORS origins for production
- [ ] Prometheus metrics endpoint

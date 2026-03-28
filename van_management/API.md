# Van Management API

This document describes the current public and local API surface for the
`van_management` service.

It covers:

1. Single truck updates
2. Batch truck updates
3. Fleet-wide reads
4. Per-truck polling and history
5. Citizen/user signals with optional image attachments

## Overview

- Service name: `van_management`
- Main route prefixes: `/api/v1/trucks`, `/api/v1/signals`
- Public base URL: `https://dayana-nonfulminating-novella.ngrok-free.dev`
- Local base URL: `http://localhost:8000`
- Public Swagger UI: `https://dayana-nonfulminating-novella.ngrok-free.dev/docs`
- Public OpenAPI schema: `https://dayana-nonfulminating-novella.ngrok-free.dev/openapi.json`
- Local Swagger UI: `http://localhost:8000/docs`
- Local OpenAPI schema: `http://localhost:8000/openapi.json`
- Content type: `application/json`
- Authentication: none at the moment

For external integrations, use the public ngrok URL above as the base URL for
all requests.
If the ngrok tunnel changes later, replace the base URL everywhere with the new
public URL.
When calling the public ngrok endpoint from scripts or API clients, include the
header `ngrok-skip-browser-warning: true`.

## Quick Start

Use these values for every external request:

- Base URL: `https://dayana-nonfulminating-novella.ngrok-free.dev`
- Required header: `ngrok-skip-browser-warning: true`
- Content type for POST requests: `application/json`
- Truck route prefix: `/api/v1/trucks`
- Signals route prefix: `/api/v1/signals`

Recommended verification flow:

1. Call `GET /health`
2. Call `GET /version`
3. Call `GET /api/v1/trucks`
4. Call `GET /api/v1/trucks/{truck_id}/latest`
5. Call `POST /api/v1/trucks/batch` for bulk truck ingestion
6. Call `POST /api/v1/signals` to create a signal

Example:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/health \
  -H "ngrok-skip-browser-warning: true"
```

## Data Model

### Single update request

```json
{
  "truck_id": "TRUCK_001",
  "waste_type": "organic",
  "current_position": {
    "latitude": 45.4642,
    "longitude": 9.19,
    "timestamp": "2026-03-28T10:15:00Z"
  }
}
```

### Batch update request

```json
{
  "company_id": "COMPANY_A",
  "updates": [
    {
      "truck_id": "TRUCK_001",
      "waste_type": "organic",
      "current_position": {
        "latitude": 45.46,
        "longitude": 9.19,
        "timestamp": "2026-03-28T10:15:00Z"
      }
    },
    {
      "truck_id": "TRUCK_002",
      "waste_type": "plastic",
      "current_position": {
        "latitude": 45.47,
        "longitude": 9.20,
        "timestamp": "2026-03-28T10:15:00Z"
      }
    }
  ]
}
```

### Truck state response object

```json
{
  "id": 2,
  "truck_id": "TRUCK_001",
  "company_id": null,
  "waste_type": "organic",
  "latitude": 45.47,
  "longitude": 9.2,
  "position_timestamp": "2026-03-28T10:20:00Z",
  "version": 2,
  "created_at": "2026-03-28T10:20:01Z"
}
```

### Batch response object

```json
{
  "company_id": "COMPANY_A",
  "accepted": 2,
  "records": [
    {
      "id": 1,
      "truck_id": "TRUCK_001",
      "company_id": "COMPANY_A",
      "waste_type": "organic",
      "latitude": 45.46,
      "longitude": 9.19,
      "position_timestamp": "2026-03-28T10:15:00Z",
      "version": 1,
      "created_at": "2026-03-28T10:15:01Z"
    },
    {
      "id": 2,
      "truck_id": "TRUCK_002",
      "company_id": "COMPANY_A",
      "waste_type": "plastic",
      "latitude": 45.47,
      "longitude": 9.2,
      "position_timestamp": "2026-03-28T10:15:00Z",
      "version": 1,
      "created_at": "2026-03-28T10:15:01Z"
    }
  ]
}
```

### Field definitions

| Field | Type | Meaning |
|---|---|---|
| `truck_id` | string | Truck identifier. Max 64 characters. |
| `company_id` | string or null | Company identifier. Present on batched rows, null for single-update ingestion. |
| `waste_type` | enum | One of `organic`, `paper`, `plastic`, `glass`, `mixed`. |
| `current_position.latitude` | float | Latitude, from `-90` to `90`. |
| `current_position.longitude` | float | Longitude, from `-180` to `180`. |
| `current_position.timestamp` | ISO 8601 datetime | Timestamp coming from the vehicle payload. |
| `updates` | array | List of truck updates for batch ingestion. Min 1, max 500 items. |
| `id` | integer | Internal database row id. |
| `position_timestamp` | ISO 8601 datetime | Vehicle event time stored by the API. |
| `version` | integer | Monotonic version number per truck. Starts at `1`. |
| `created_at` | ISO 8601 datetime | Time the record was inserted into the backend database. |
| `accepted` | integer | Number of rows accepted in a batch request. |

## Response Envelope

Successful API responses use the same wrapper:

```json
{
  "success": true,
  "message": "Human-readable status message",
  "data": {}
}
```

Validation and explicit HTTP errors use FastAPI's standard error format.

## Endpoint Summary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/version` | Service metadata |
| `GET` | `/api/v1/trucks` | Fleet-wide latest state snapshot |
| `GET` | `/api/v1/trucks/ids` | List all known truck IDs |
| `GET` | `/api/v1/trucks/{truck_id}/latest` | Fetch the current state for one truck |
| `GET` | `/api/v1/trucks/{truck_id}/history` | Fetch version history for one truck |
| `POST` | `/api/v1/trucks/update` | Create a new truck state version |
| `POST` | `/api/v1/trucks/batch` | Create many truck state versions in one request |
| `POST` | `/api/v1/signals` | Create a new signal |
| `GET` | `/api/v1/signals` | List signals |
| `GET` | `/api/v1/signals/{signal_id}` | Fetch one signal with attachments |
| `POST` | `/api/v1/signals/{signal_id}/attachments` | Upload one or more signal images |
| `GET` | `/api/v1/signals/{signal_id}/attachments/{attachment_id}` | Download an attachment |
| `DELETE` | `/api/v1/signals/{signal_id}` | Delete a signal and its attachments |

## Meta Endpoints

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

## Fleet Read Endpoints

### `GET /api/v1/trucks`

Returns one latest row per known truck.

Behavior:

- Returns `200 OK` with an empty list when no trucks exist yet
- Returns one row per truck, not full history
- Useful for dashboards or a full current-state sync

Example:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks \
  -H "ngrok-skip-browser-warning: true"
```

### `GET /api/v1/trucks/ids`

Returns a flat list of all known `truck_id` values.

Example:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/ids \
  -H "ngrok-skip-browser-warning: true"
```

## Single Update Ingestion

### `POST /api/v1/trucks/update`

Creates a new state version for a single truck.

Example:

```bash
curl -X POST https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/update \
  -H "ngrok-skip-browser-warning: true" \
  -H "Content-Type: application/json" \
  -d '{
    "truck_id": "TRUCK_001",
    "waste_type": "organic",
    "current_position": {
      "latitude": 45.4642,
      "longitude": 9.19,
      "timestamp": "2026-03-28T10:15:00Z"
    }
  }'
```

Behavior:

- Creates exactly one new versioned row
- Repeated payloads still create new versions
- `company_id` is `null` on rows created by this endpoint

## Batch Ingestion

### `POST /api/v1/trucks/batch`

Accepts up to 500 truck updates in one request under a `company_id`.

Behavior:

- All rows are inserted in one transaction
- Duplicate `truck_id` values inside the same batch stack versions correctly
- Existing truck versions continue correctly if the truck already has history
- Each returned record includes the submitted `company_id`

Example:

```bash
curl -X POST https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/batch \
  -H "ngrok-skip-browser-warning: true" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "COMPANY_A",
    "updates": [
      {
        "truck_id": "TRUCK_001",
        "waste_type": "organic",
        "current_position": {
          "latitude": 45.46,
          "longitude": 9.19,
          "timestamp": "2026-03-28T10:15:00Z"
        }
      },
      {
        "truck_id": "TRUCK_002",
        "waste_type": "plastic",
        "current_position": {
          "latitude": 45.47,
          "longitude": 9.20,
          "timestamp": "2026-03-28T10:15:00Z"
        }
      }
    ]
  }'
```

## Per-Truck Read Endpoints

### `GET /api/v1/trucks/{truck_id}/latest`

Returns the newest stored state for one truck.

This is the recommended endpoint for once-per-second polling.

Example:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/TRUCK_001/latest \
  -H "ngrok-skip-browser-warning: true"
```

Recommended client behavior:

1. Poll `/latest`
2. Track the last seen `version`
3. Process only newer versions

### `GET /api/v1/trucks/{truck_id}/history`

Returns version history for a truck from newest to oldest.

Query parameters:

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `page` | integer | `1` | Must be `>= 1` |
| `page_size` | integer | `50` | Must be between `1` and `200` |

Example:

```bash
curl "https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/TRUCK_001/history?page=1&page_size=50" \
  -H "ngrok-skip-browser-warning: true"
```

Use history for:

- backfill after downtime
- auditing
- debugging version progression

## Validation And Errors

### `404 Not Found`

Returned when the requested truck has no stored data yet.

### `422 Unprocessable Entity`

Typical causes:

- invalid `waste_type`
- latitude outside `-90..90`
- longitude outside `-180..180`
- missing required fields
- invalid timestamp format
- missing `company_id` on batch ingestion
- empty `updates` array on batch ingestion
- more than 500 updates in one batch

Signals validation:

- `signal_type` must be `emergenza` or `info`
- signal title must be 1-200 characters
- signal description must be 1-5000 characters
- signal attachments accept only `image/jpeg`, `image/png`, `image/webp`, `image/gif`
- at most 10 files per upload request
- at most 10 MB per file

## Public Access Notes

- The public URL is currently served through ngrok free tier
- API clients should include `ngrok-skip-browser-warning: true`
- If the ngrok tunnel changes, all consumers must switch to the new base URL
- If the public URL returns `502`, the tunnel is likely no longer pointing to local port `8000`

## Integration Example

### Python polling example

```python
import time
import requests

BASE_URL = "https://dayana-nonfulminating-novella.ngrok-free.dev"
truck_id = "TRUCK_001"
last_version = 0

while True:
    response = requests.get(
        f"{BASE_URL}/api/v1/trucks/{truck_id}/latest",
        headers={"ngrok-skip-browser-warning": "true"},
        timeout=5,
    )

    if response.status_code == 404:
        time.sleep(1)
        continue

    response.raise_for_status()
    state = response.json()["data"]

    if state["version"] > last_version:
        last_version = state["version"]
        print("New state:", state)

    time.sleep(1)
```

For the fully detailed handoff guide, see `API_REFERENCE.md`.

## Signals Quick Reference

### `POST /api/v1/signals`

Creates a geolocated signal.

```bash
curl -X POST https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals \
  -H "ngrok-skip-browser-warning: true" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Incendio boschivo",
    "description": "Fumo visibile dalla strada provinciale SP45, lato nord",
    "signal_type": "emergenza",
    "latitude": 45.4642,
    "longitude": 9.19
  }'
```

### `POST /api/v1/signals/{signal_id}/attachments`

Uploads one or more images to a signal using `multipart/form-data`.

```bash
curl -X POST https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals/1/attachments \
  -H "ngrok-skip-browser-warning: true" \
  -F "files=@photo1.jpg;type=image/jpeg" \
  -F "files=@photo2.png;type=image/png"
```

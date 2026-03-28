# Van Management API Reference

This document is the handoff guide for clients that need to read truck data from
the `van_management` service.

It is written for integrators who need to:

1. Send single or batched truck telemetry updates into the service.
2. Read the latest state for one truck or for the whole fleet.
3. Poll current truck information through the public ngrok URL.

## Overview

- Service name: `van_management`
- Base route prefix: `/api/v1/trucks`
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
If the ngrok tunnel is rotated later, replace the base URL everywhere with the
new public URL.
When calling the public ngrok endpoint from scripts or API clients, include the
header `ngrok-skip-browser-warning: true` to avoid the free-tier browser
warning page.
The active public tunnel is expected to forward to the FastAPI service running
on local port `8000`.

## Quick Start For External Clients

Use these values for every external request:

- Base URL: `https://dayana-nonfulminating-novella.ngrok-free.dev`
- Required header: `ngrok-skip-browser-warning: true`
- Content type for POST requests: `application/json`
- Route prefix: `/api/v1/trucks`

Recommended verification flow:

1. Call `GET /health` to verify reachability.
2. Call `GET /version` to confirm the correct service is behind the tunnel.
3. Call `GET /api/v1/trucks` to retrieve the current fleet snapshot.
4. Call `GET /api/v1/trucks/{truck_id}/latest` for per-truck polling.
5. Call `POST /api/v1/trucks/batch` when your producer needs to send many
   updates in one request.

Example:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/health \
  -H "ngrok-skip-browser-warning: true"
```

## What The API Stores

Every truck update is stored as a new immutable row.

That means:

- There is no in-place overwrite of the previous state.
- Each update increments the truck `version`.
- The latest state is the row with the highest `version` for that `truck_id`.
- Full audit history stays available through the history endpoint.
- Batch ingestion stores all submitted rows in one transaction.
- Batch-ingested rows also store the `company_id` that submitted them.

## Response Envelope

Successful API responses use the same wrapper:

```json
{
  "success": true,
  "message": "Human-readable status message",
  "data": {}
}
```

Error responses from FastAPI validation or explicit `HTTPException` use the
standard FastAPI format instead of the wrapper.

Example `404`:

```json
{
  "detail": "No current state found for truck 'TRUCK_001'"
}
```

Example `422`:

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

## Data Models

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
| `company_id` | string or null | Company identifier. Present on batched rows, null for rows created by single-update ingestion. |
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

## Health And Metadata

### `GET /health`

Use this to check whether the API is reachable.

Example request:

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

Returns service name and version.

Example request:

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

Returns one latest row per known truck. This is the fleet-wide snapshot
endpoint.

Behavior:

- Returns `200 OK` with an empty list when no trucks exist yet.
- Returns one row per truck, not full history.
- Useful for dashboards or a quick current-state sync of the entire fleet.

Example request:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks \
  -H "ngrok-skip-browser-warning: true"
```

Example response:

```json
{
  "success": true,
  "message": "Found 2 truck(s)",
  "data": [
    {
      "id": 3,
      "truck_id": "TRUCK_001",
      "company_id": null,
      "waste_type": "organic",
      "latitude": 45.47,
      "longitude": 9.2,
      "position_timestamp": "2026-03-28T10:20:00Z",
      "version": 3,
      "created_at": "2026-03-28T10:20:01Z"
    },
    {
      "id": 5,
      "truck_id": "TRUCK_002",
      "company_id": null,
      "waste_type": "plastic",
      "latitude": 45.48,
      "longitude": 9.21,
      "position_timestamp": "2026-03-28T10:20:00Z",
      "version": 2,
      "created_at": "2026-03-28T10:20:01Z"
    }
  ]
}
```

### `GET /api/v1/trucks/ids`

Returns a flat list of all known `truck_id` values.

Behavior:

- Returns `200 OK` with an empty list when no trucks exist yet.
- IDs are derived from the current fleet snapshot.

Example request:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/ids \
  -H "ngrok-skip-browser-warning: true"
```

Example response:

```json
{
  "success": true,
  "message": "Found 2 truck ID(s)",
  "data": ["TRUCK_001", "TRUCK_002"]
}
```

## Single Update Ingestion

### `POST /api/v1/trucks/update`

Creates a new state version for a single truck.

Example request:

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

Success response:

Status: `201 Created`

```json
{
  "success": true,
  "message": "Truck TRUCK_001 updated to version 1",
  "data": {
    "id": 1,
    "truck_id": "TRUCK_001",
    "company_id": null,
    "waste_type": "organic",
    "latitude": 45.4642,
    "longitude": 9.19,
    "position_timestamp": "2026-03-28T10:15:00Z",
    "version": 1,
    "created_at": "2026-03-28T10:15:01Z"
  }
}
```

Behavior notes:

- A second update for the same `truck_id` creates `version = 2`.
- A third update creates `version = 3`, and so on.
- The API does not deduplicate repeated payloads.
- Rows created by this endpoint return `company_id: null`.
- The implementation retries briefly on version conflicts caused by concurrent
  writers.

## Batch Ingestion

### `POST /api/v1/trucks/batch`

Accepts up to 500 truck updates in one request, grouped under a `company_id`.

Behavior:

- All rows are inserted in a single transaction.
- If the same `truck_id` appears more than once inside the batch, versions are
  incremented correctly within the batch itself.
- Existing truck versions are continued correctly when a batch includes trucks
  that already have history.
- The response contains all inserted records and their assigned versions.

Example request:

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

Success response:

Status: `201 Created`

```json
{
  "success": true,
  "message": "Accepted 2 update(s) from 'COMPANY_A'",
  "data": {
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
}
```

Validation notes:

- `company_id` is required.
- `updates` must contain between 1 and 500 items.
- The same field validation rules from single-update payloads also apply inside
  the batch.

## Per-Truck Read Endpoints

### `GET /api/v1/trucks/{truck_id}/latest`

Returns the newest stored state for one truck. This is the recommended
endpoint for clients that poll every second.

Example request:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/TRUCK_001/latest \
  -H "ngrok-skip-browser-warning: true"
```

Success response:

Status: `200 OK`

```json
{
  "success": true,
  "message": "Latest state for truck 'TRUCK_001'",
  "data": {
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
}
```

Not found response:

Status: `404 Not Found`

```json
{
  "detail": "No current state found for truck 'UNKNOWN'"
}
```

Recommended polling pattern:

1. Poll `/api/v1/trucks/{truck_id}/latest`.
2. Compare the returned `version` with the last version already processed.
3. Process the row only when `version` increases.
4. Use `position_timestamp` as the vehicle event time.
5. Use `created_at` as the backend ingest time.

This avoids downloading full history every second.

### `GET /api/v1/trucks/{truck_id}/history`

Returns version history for a truck from newest to oldest.

Query parameters:

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `page` | integer | `1` | Must be `>= 1` |
| `page_size` | integer | `50` | Must be between `1` and `200` |

Example request:

```bash
curl "https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/trucks/TRUCK_001/history?page=1&page_size=50" \
  -H "ngrok-skip-browser-warning: true"
```

Success response:

Status: `200 OK`

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
        "company_id": null,
        "waste_type": "organic",
        "latitude": 45.47,
        "longitude": 9.2,
        "position_timestamp": "2026-03-28T10:20:00Z",
        "version": 2,
        "created_at": "2026-03-28T10:20:01Z"
      },
      {
        "id": 1,
        "truck_id": "TRUCK_001",
        "company_id": null,
        "waste_type": "organic",
        "latitude": 45.4642,
        "longitude": 9.19,
        "position_timestamp": "2026-03-28T10:15:00Z",
        "version": 1,
        "created_at": "2026-03-28T10:15:01Z"
      }
    ]
  }
}
```

Not found response:

Status: `404 Not Found`

```json
{
  "detail": "No history found for truck 'UNKNOWN'"
}
```

When to use history:

- backfill after downtime
- audit / traceability
- a full timeline of updates for one truck
- debugging version progression

Do not use history for once-per-second polling unless the client explicitly
needs more than the newest state.

## Error Handling

### `404 Not Found`

Returned when the requested truck has no stored data yet.

### `422 Unprocessable Entity`

Returned when the payload fails validation.

Typical causes:

- invalid `waste_type`
- latitude outside `-90..90`
- longitude outside `-180..180`
- missing required fields
- invalid timestamp format
- missing `company_id` on batch ingestion
- empty `updates` array on batch ingestion
- more than 500 updates in one batch

## Public Access Notes

- The public URL is currently served through ngrok free tier.
- Scripted/API access should include `ngrok-skip-browser-warning: true`.
- If the ngrok tunnel is restarted with a different hostname, all consumers must
  switch to the new base URL.
- If the public URL returns `502`, the tunnel is likely active but not pointing
  at the local backend on port `8000`.

## Integration Examples

### JavaScript polling example

```js
const BASE_URL = "https://dayana-nonfulminating-novella.ngrok-free.dev";
const truckId = "TRUCK_001";
let lastVersion = 0;

async function pollTruck() {
  const response = await fetch(`${BASE_URL}/api/v1/trucks/${truckId}/latest`, {
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
  });

  if (response.status === 404) {
    return;
  }

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const body = await response.json();
  const state = body.data;

  if (state.version > lastVersion) {
    lastVersion = state.version;
    console.log("New truck state", state);
  }
}

setInterval(() => {
  pollTruck().catch(console.error);
}, 1000);
```

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
    body = response.json()
    state = body["data"]

    if state["version"] > last_version:
        last_version = state["version"]
        print("New state:", state)

    time.sleep(1)
```

## Operational Notes

- The API currently supports polling, not push delivery.
- There is no authentication yet, so place the service behind a trusted network
  boundary or gateway if needed.
- The current public tunnel URL is
  `https://dayana-nonfulminating-novella.ngrok-free.dev`.
- The batch endpoint accepts up to 500 updates in one request.
- The API now exposes both per-truck and fleet-wide latest-state reads.
- If a fleet-wide snapshot or push stream is needed later, a dedicated endpoint
  or WebSocket/SSE channel would be a natural next step.

---

# Signals API Reference

Signals allow users to report geolocated events such as emergencies or
informational notices. Each signal has a position, a type, a title, a
description, and optionally one or more image attachments.

## Signals Overview

- Route prefix: `/api/v1/signals`
- Signal types: `emergenza`, `info`
- Attachments: uploaded separately via multipart form data after signal creation
- Accepted image types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`
- Max file size: 10 MB per image
- Max files per upload: 10

## Signals Endpoint Summary

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/signals` | Create a new signal |
| `GET` | `/api/v1/signals` | List all signals (paginated) |
| `GET` | `/api/v1/signals/{signal_id}` | Get a single signal with attachments |
| `POST` | `/api/v1/signals/{signal_id}/attachments` | Upload image attachments |
| `GET` | `/api/v1/signals/{signal_id}/attachments/{attachment_id}` | Download an image |
| `DELETE` | `/api/v1/signals/{signal_id}` | Delete a signal and its attachments |

## Signals Data Models

### Signal create request

```json
{
  "title": "Incendio boschivo",
  "description": "Fumo visibile dalla strada provinciale SP45, lato nord",
  "signal_type": "emergenza",
  "latitude": 45.4642,
  "longitude": 9.19
}
```

### Signal response object

```json
{
  "id": 1,
  "title": "Incendio boschivo",
  "description": "Fumo visibile dalla strada provinciale SP45, lato nord",
  "signal_type": "emergenza",
  "latitude": 45.4642,
  "longitude": 9.19,
  "created_at": "2026-03-28T10:15:00Z",
  "attachments": [
    {
      "id": 1,
      "signal_id": 1,
      "original_filename": "foto_incendio.jpg",
      "content_type": "image/jpeg",
      "file_size": 245000,
      "created_at": "2026-03-28T10:16:00Z"
    }
  ]
}
```

### Signal list response

```json
{
  "total": 5,
  "page": 1,
  "page_size": 50,
  "signals": [
    { "...signal object..." }
  ]
}
```

### Attachment response object (from upload)

```json
{
  "id": 1,
  "signal_id": 1,
  "original_filename": "foto_incendio.jpg",
  "content_type": "image/jpeg",
  "file_size": 245000,
  "created_at": "2026-03-28T10:16:00Z"
}
```

### Signals field definitions

| Field | Type | Meaning |
|---|---|---|
| `title` | string | Signal title. Max 200 characters. |
| `description` | string | Signal description. Max 5000 characters. |
| `signal_type` | enum | One of `emergenza`, `info`. |
| `latitude` | float | Latitude, from `-90` to `90`. |
| `longitude` | float | Longitude, from `-180` to `180`. |
| `id` | integer | Internal database row id. |
| `created_at` | ISO 8601 datetime | Time the signal was created. |
| `attachments` | array | List of attachment objects. Empty when no images uploaded. |
| `original_filename` | string | Original name of the uploaded file. |
| `content_type` | string | MIME type of the uploaded file. |
| `file_size` | integer | Size in bytes of the uploaded file. |

## Create Signal

### `POST /api/v1/signals`

Creates a new signal.

Example request:

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

Success response:

Status: `201 Created`

```json
{
  "success": true,
  "message": "Signal 1 created",
  "data": {
    "id": 1,
    "title": "Incendio boschivo",
    "description": "Fumo visibile dalla strada provinciale SP45, lato nord",
    "signal_type": "emergenza",
    "latitude": 45.4642,
    "longitude": 9.19,
    "created_at": "2026-03-28T10:15:00Z",
    "attachments": []
  }
}
```

## List Signals

### `GET /api/v1/signals`

Returns all signals ordered by newest first, with pagination.

Query parameters:

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `page` | integer | `1` | Must be `>= 1` |
| `page_size` | integer | `50` | Must be between `1` and `200` |

Example request:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals \
  -H "ngrok-skip-browser-warning: true"
```

Success response:

Status: `200 OK`

```json
{
  "success": true,
  "message": "Found 2 signal(s)",
  "data": {
    "total": 2,
    "page": 1,
    "page_size": 50,
    "signals": [
      {
        "id": 2,
        "title": "Cassonetto pieno",
        "description": "Cassonetto organico stracolmo in via Roma 12",
        "signal_type": "info",
        "latitude": 45.47,
        "longitude": 9.2,
        "created_at": "2026-03-28T10:20:00Z",
        "attachments": []
      },
      {
        "id": 1,
        "title": "Incendio boschivo",
        "description": "Fumo visibile dalla strada provinciale SP45, lato nord",
        "signal_type": "emergenza",
        "latitude": 45.4642,
        "longitude": 9.19,
        "created_at": "2026-03-28T10:15:00Z",
        "attachments": []
      }
    ]
  }
}
```

Behavior:

- Returns `200 OK` with `total: 0` and empty `signals` list when no signals
  exist yet.
- Returns newest signals first.

## Get Single Signal

### `GET /api/v1/signals/{signal_id}`

Returns a signal with its attachment metadata.

Example request:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals/1 \
  -H "ngrok-skip-browser-warning: true"
```

Success response:

Status: `200 OK`

```json
{
  "success": true,
  "message": "Signal 1",
  "data": {
    "id": 1,
    "title": "Incendio boschivo",
    "description": "Fumo visibile dalla strada provinciale SP45, lato nord",
    "signal_type": "emergenza",
    "latitude": 45.4642,
    "longitude": 9.19,
    "created_at": "2026-03-28T10:15:00Z",
    "attachments": [
      {
        "id": 1,
        "signal_id": 1,
        "original_filename": "foto_incendio.jpg",
        "content_type": "image/jpeg",
        "file_size": 245000,
        "created_at": "2026-03-28T10:16:00Z"
      }
    ]
  }
}
```

Not found response:

Status: `404 Not Found`

```json
{
  "detail": "Signal 99 not found"
}
```

## Upload Attachments

### `POST /api/v1/signals/{signal_id}/attachments`

Upload one or more image files to an existing signal.

**Important:** This endpoint uses `multipart/form-data`, not JSON.

Constraints:

- Accepted MIME types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`
- Maximum file size: 10 MB per file
- Maximum files per request: 10

Example request:

```bash
curl -X POST https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals/1/attachments \
  -H "ngrok-skip-browser-warning: true" \
  -F "files=@foto_incendio.jpg;type=image/jpeg" \
  -F "files=@foto_dettaglio.png;type=image/png"
```

Success response:

Status: `201 Created`

```json
{
  "success": true,
  "message": "2 attachment(s) uploaded to signal 1",
  "data": [
    {
      "id": 1,
      "signal_id": 1,
      "original_filename": "foto_incendio.jpg",
      "content_type": "image/jpeg",
      "file_size": 245000,
      "created_at": "2026-03-28T10:16:00Z"
    },
    {
      "id": 2,
      "signal_id": 1,
      "original_filename": "foto_dettaglio.png",
      "content_type": "image/png",
      "file_size": 189000,
      "created_at": "2026-03-28T10:16:00Z"
    }
  ]
}
```

Error responses:

- `404 Not Found` — signal does not exist
- `400 Bad Request` — invalid content type or file too large

Example `400`:

```json
{
  "detail": "File 'document.pdf': content type 'application/pdf' not allowed. Accepted: image/gif, image/jpeg, image/png, image/webp"
}
```

## Download Attachment

### `GET /api/v1/signals/{signal_id}/attachments/{attachment_id}`

Returns the image file as a binary download.

Example request:

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals/1/attachments/1 \
  -H "ngrok-skip-browser-warning: true" \
  --output foto_incendio.jpg
```

Success response:

Status: `200 OK`

The response body is the raw image file. The `Content-Type` header matches the
original upload MIME type. The `Content-Disposition` header contains the
original filename.

Not found response:

Status: `404 Not Found`

```json
{
  "detail": "Attachment 99 not found for signal 1"
}
```

## Delete Signal

### `DELETE /api/v1/signals/{signal_id}`

Deletes a signal and all its attachments (both database records and files on
disk).

Example request:

```bash
curl -X DELETE https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals/1 \
  -H "ngrok-skip-browser-warning: true"
```

Success response:

Status: `200 OK`

```json
{
  "success": true,
  "message": "Signal 1 deleted",
  "data": null
}
```

Not found response:

Status: `404 Not Found`

```json
{
  "detail": "Signal 1 not found"
}
```

## Signals Integration Example

Complete flow: create a signal, upload images, then retrieve it.

### Step 1 — Create the signal

```bash
curl -X POST https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals \
  -H "ngrok-skip-browser-warning: true" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Discarica abusiva",
    "description": "Rifiuti abbandonati nel parcheggio di via Verdi",
    "signal_type": "emergenza",
    "latitude": 45.4642,
    "longitude": 9.19
  }'
```

Save the returned `id` (e.g., `3`).

### Step 2 — Upload images

```bash
curl -X POST https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals/3/attachments \
  -H "ngrok-skip-browser-warning: true" \
  -F "files=@foto1.jpg;type=image/jpeg" \
  -F "files=@foto2.jpg;type=image/jpeg"
```

### Step 3 — Retrieve the signal with attachments

```bash
curl https://dayana-nonfulminating-novella.ngrok-free.dev/api/v1/signals/3 \
  -H "ngrok-skip-browser-warning: true"
```

### JavaScript upload example

```js
const BASE_URL = "https://dayana-nonfulminating-novella.ngrok-free.dev";
const HEADERS = { "ngrok-skip-browser-warning": "true" };

// Step 1: create signal
const signalResp = await fetch(`${BASE_URL}/api/v1/signals`, {
  method: "POST",
  headers: { ...HEADERS, "Content-Type": "application/json" },
  body: JSON.stringify({
    title: "Discarica abusiva",
    description: "Rifiuti abbandonati nel parcheggio",
    signal_type: "emergenza",
    latitude: 45.4642,
    longitude: 9.19,
  }),
});
const { data: signal } = await signalResp.json();

// Step 2: upload images
const formData = new FormData();
formData.append("files", imageFile1); // File or Blob
formData.append("files", imageFile2);

const uploadResp = await fetch(
  `${BASE_URL}/api/v1/signals/${signal.id}/attachments`,
  { method: "POST", headers: HEADERS, body: formData }
);
const { data: attachments } = await uploadResp.json();
console.log("Uploaded", attachments.length, "image(s)");

// Step 3: download an image
const imgResp = await fetch(
  `${BASE_URL}/api/v1/signals/${signal.id}/attachments/${attachments[0].id}`,
  { headers: HEADERS }
);
const blob = await imgResp.blob();
const imgUrl = URL.createObjectURL(blob);
```

### Python upload example

```python
import httpx

BASE_URL = "https://dayana-nonfulminating-novella.ngrok-free.dev"
HEADERS = {"ngrok-skip-browser-warning": "true"}

with httpx.Client(headers=HEADERS) as client:
    # Step 1: create signal
    signal_resp = client.post(
        f"{BASE_URL}/api/v1/signals",
        json={
            "title": "Discarica abusiva",
            "description": "Rifiuti abbandonati nel parcheggio",
            "signal_type": "emergenza",
            "latitude": 45.4642,
            "longitude": 9.19,
        },
    )
    signal_id = signal_resp.json()["data"]["id"]

    # Step 2: upload images
    with open("foto1.jpg", "rb") as f1, open("foto2.jpg", "rb") as f2:
        upload_resp = client.post(
            f"{BASE_URL}/api/v1/signals/{signal_id}/attachments",
            files=[
                ("files", ("foto1.jpg", f1, "image/jpeg")),
                ("files", ("foto2.jpg", f2, "image/jpeg")),
            ],
        )
    print("Uploaded:", upload_resp.json()["data"])

    # Step 3: download an image
    att_id = upload_resp.json()["data"][0]["id"]
    img_resp = client.get(
        f"{BASE_URL}/api/v1/signals/{signal_id}/attachments/{att_id}"
    )
    with open("downloaded.jpg", "wb") as out:
        out.write(img_resp.content)
```

## Signals Error Handling

### `404 Not Found`

Returned when the requested signal or attachment does not exist.

### `400 Bad Request`

Returned when an attachment upload fails validation:

- File content type not in the accepted list
- File exceeds the 10 MB size limit
- More than 10 files in one upload request

### `422 Unprocessable Entity`

Returned when the signal creation payload fails validation:

- Invalid `signal_type` (must be `emergenza` or `info`)
- Latitude outside `-90..90`
- Longitude outside `-180..180`
- Missing or empty `title`
- Missing or empty `description`

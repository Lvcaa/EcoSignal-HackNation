---
phase: 01-green-buddy-ux
plan: 03
subsystem: backend
tags: [fastapi, anthropic, claude-vision, image-analysis, microservice]

# Dependency graph
requires:
  - phase: 01-green-buddy-ux/01
    provides: backend auth/profile fields for JWT-protected endpoints
  - phase: 01-green-buddy-ux/02
    provides: onboarding flow that establishes user profiles
provides:
  - image-analyzer microservice with Claude Vision API integration
  - meal, grocery, clothing photo analysis with CO2 estimation
  - text-description fallback when no photo provided
  - API gateway /api/v1/image/analyze proxy endpoint
affects: [04-daily-tracking-ui, 05-dashboard-narrative]

# Tech tracking
tech-stack:
  added: [anthropic-sdk, tenacity]
  patterns: [Claude Vision base64 image analysis, Italian-language system prompts, fallback on error, tenacity retry with exponential backoff]

key-files:
  created:
    - image-analyzer/app/__init__.py
    - image-analyzer/app/main.py
    - image-analyzer/app/config.py
    - image-analyzer/app/schemas.py
    - image-analyzer/app/router.py
    - image-analyzer/app/service.py
    - image-analyzer/app/prompts.py
    - image-analyzer/Dockerfile
    - image-analyzer/requirements.txt
  modified:
    - docker-compose.yml
    - api-gateway/app/config.py
    - api-gateway/app/router.py
    - api-gateway/app/main.py

key-decisions:
  - "Claude Vision API (Anthropic SDK) for image analysis"
  - "Port 8008 for image-analyzer service"
  - "Three analysis types: meal, grocery, clothing with Italian-language prompts"
  - "Optional[str] used for image_base64 and user_description for Python 3.9 compatibility"
  - "Fallback response with is_fallback=True and empty items on any error"
  - "Rate limit 20/minute on image analyze endpoint"

patterns-established:
  - "Italian-language system prompts for Claude Vision with JSON-only output format"
  - "CO2 factors embedded in prompts for food (per gram) and clothing (per item lifecycle)"
  - "Text-description fallback: user_description can substitute for image_base64"

issues-created: []

# Metrics
duration: 10min
completed: 2026-03-28
---

# Plan 03: Image Analyzer Microservice Summary

**New image-analyzer service using Claude Vision API for meal, grocery, and clothing photo analysis with CO2 estimation**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-28
- **Completed:** 2026-03-28
- **Tasks:** 3
- **Files created:** 9
- **Files modified:** 4

## Accomplishments
- Scaffolded image-analyzer microservice following ai-narrative patterns (FastAPI, port 8008)
- Created comprehensive Pydantic schemas for 3 analysis types (meal, grocery, clothing)
- Implemented Claude Vision analysis logic with tenacity retry (3 attempts, exponential backoff)
- Created Italian-language system prompts with embedded CO2 factors per analysis type
- Added text-description fallback when no photo is provided
- Integrated into API gateway with JWT auth and 20/minute rate limit
- Added image-analyzer to docker-compose.yml with health check and redis dependency

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold image-analyzer service** - `36efe07` (feat)
2. **Task 2: Implement Claude Vision analysis logic** - `01ae922` (feat)
3. **Task 3: Add image analysis routes to API gateway** - `1f0ee96` (feat)

## Files Created/Modified
- `image-analyzer/app/main.py` - FastAPI app entry point with health endpoint
- `image-analyzer/app/config.py` - Settings: ANTHROPIC_API_KEY, MODEL_NAME, LOG_LEVEL
- `image-analyzer/app/schemas.py` - All request/response models for 3 analysis types
- `image-analyzer/app/router.py` - POST /api/v1/analyze endpoint
- `image-analyzer/app/service.py` - Claude Vision analysis with retry and fallback
- `image-analyzer/app/prompts.py` - Italian system prompts with CO2 factors
- `image-analyzer/Dockerfile` - Python 3.12-slim, port 8008
- `image-analyzer/requirements.txt` - FastAPI, Anthropic SDK, tenacity, httpx
- `docker-compose.yml` - Added image-analyzer service and IMAGE_ANALYZER_SERVICE_URL env var
- `api-gateway/app/config.py` - Added image_analyzer_service_url setting
- `api-gateway/app/router.py` - Added image_router with /image/analyze proxy endpoint
- `api-gateway/app/main.py` - Registered image_router

## Decisions Made
- Claude Vision API via Anthropic SDK for image analysis (consistent with ai-narrative)
- Port 8008 to avoid conflicts with existing services (8001-8007)
- Italian-language prompts with JSON-only output format
- CO2 factors: food per gram, grocery per kg, clothing per item lifecycle
- Used Optional[] instead of | None for Python 3.9 runtime compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Python 3.9 union syntax incompatibility**
- **Found during:** Task 1 verification
- **Issue:** `str | None` syntax in Pydantic models fails at runtime on Python 3.9 despite `from __future__ import annotations`
- **Fix:** Changed to `Optional[str]` and `Union[...]` from typing module
- **Verification:** Schema imports pass successfully

---

**Total deviations:** 1 auto-fixed (1 blocking), 0 deferred
**Impact on plan:** Minor syntax fix, no architectural change.

## Next Phase Readiness
- Image analyzer service fully functional with 3 analysis types
- API gateway proxies requests with JWT auth
- Ready for Plan 04 (Daily Tracking UI) to build frontend for photo capture and analysis

---
*Phase: 01-green-buddy-ux*
*Completed: 2026-03-28*

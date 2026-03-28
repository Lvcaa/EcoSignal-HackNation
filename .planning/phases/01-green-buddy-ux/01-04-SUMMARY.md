---
phase: 01-green-buddy-ux
plan: 04
subsystem: full-stack
tags: [fastapi, react, action-logging, co2-tracking, image-analysis, mobile-ux]

# Dependency graph
requires:
  - phase: 01-green-buddy-ux/01
    provides: backend auth/profile for JWT-protected endpoints
  - phase: 01-green-buddy-ux/03
    provides: image-analyzer service for meal/grocery/clothing photo analysis
provides:
  - ActionLog model with CO2 delta tracking per action
  - POST /actions/log, GET /actions/daily, GET /actions/weekly endpoints
  - API gateway proxy routes for new action endpoints
  - ActionHub page with 4 category cards (meal, trip, grocery, clothing)
  - LogMeal, LogTrip, LogGrocery, LogClothing pages with photo capture + text input
  - BottomNav updated to 5 tabs including Azioni
affects: [05-dashboard-narrative, weekly-surveys]

# Tech tracking
new_deps: []
new_env_vars: []
new_ports: []
new_services: []
migration_needed: true  # ActionLog table added — requires DB volume reset
---

# Plan 04 Summary — Daily Action Tracking

## What was built

### Backend: actions-engine extensions
- **ActionLog model** (`actions-engine/app/models.py`): New table for logging individual user actions with CO2 delta, action type (meal/trip/grocery/clothing/appliance), optional image analysis reference, and flexible JSON metadata
- **New schemas** (`schemas.py`): ActionType enum, LogActionRequest, ActionLogResponse, DailyActionsResponse, WeeklySummaryEntry/Response
- **Repository layer** (`repository.py`): create_action_log(), get_actions_by_date(), get_actions_by_date_range()
- **Service layer** (`service.py`): build_daily_response(), build_weekly_summary() pure functions
- **Router** (`router.py`): POST /actions/log, GET /actions/daily, GET /actions/weekly — all existing catalogue/completion/streak endpoints preserved
- **API Gateway** (`api-gateway/app/router.py`): New proxy routes /actions/log, /actions/daily, /actions/weekly with user_id injection from JWT

### Frontend: action logging UI
- **ActionHub** (`frontend/src/pages/ActionHub.jsx`): Central page showing today's action count + total CO2, 4 category cards, recent actions list
- **LogMeal** (`frontend/src/pages/LogMeal.jsx`): Photo capture or text description → image-analyzer API → result display → save
- **LogTrip** (`frontend/src/pages/LogTrip.jsx`): Transport mode selector + km input → local CO2 calculation (car=0.21, transit=0.089, bike=0, walk=0 kg/km)
- **LogGrocery** (`frontend/src/pages/LogGrocery.jsx`): Photo/text → image-analyzer → save
- **LogClothing** (`frontend/src/pages/LogClothing.jsx`): Photo/text → image-analyzer → save
- **imageAnalyzer.js** (`frontend/src/api/imageAnalyzer.js`): API wrapper for POST /image/analyze
- **actions.js**: Added logAction(), getDailyActions(), getWeeklySummary()
- **useDashboard.js**: Added useLogAction(), useDailyActions(), useWeeklySummary() hooks
- **App.jsx**: 5 new protected routes (/actions, /actions/meal, /actions/trip, /actions/grocery, /actions/clothing)
- **BottomNav.jsx**: Updated from 4 to 5 tabs (Home, Azioni, Community, Progress, Profilo)

## Bug fix during verification
- Frontend was reading `analysis.co2_estimate_kg` but image-analyzer returns `analysis.result.total_co2_kg` — fixed field mapping in all 3 photo-based log pages

## Commits
- `49e1db4` feat(01-04): extend actions-engine with action logging and CO2 delta tracking
- `a3b1e81` feat(01-04): build action logging UI with photo capture and text input
- `c19b04d` fix(01-04): align frontend with image-analyzer response schema

## Deviations
- Fixed response field name mismatch between image-analyzer and frontend (auto-fix, not in original plan)
- Removed unused `analysis.summary` display from log pages (image-analyzer doesn't return a summary field)

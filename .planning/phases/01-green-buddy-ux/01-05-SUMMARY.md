---
phase: 01-green-buddy-ux
plan: 05
subsystem: api, ui
tags: [fastapi, react, tailwind, co2-factors, appliance-tracking]

# Dependency graph
requires:
  - phase: 01-green-buddy-ux
    provides: actions-engine service with ActionLog model, Dashboard with action feed
provides:
  - Weekly survey backend with appliance CO2 calculation
  - WeeklySurvey UI page with Italian labels
  - Dashboard survey prompt/results integration
  - API gateway proxy routes for weekly-survey endpoints
affects: [01-green-buddy-ux]

# Tech tracking
tech-stack:
  added: []
  patterns: [appliance CO2 factors per cycle/temp/mode, stepper UI for cycle counts]

key-files:
  created: [frontend/src/pages/WeeklySurvey.jsx, frontend/src/hooks/useDashboard.js]
  modified: [footprint-engine/app/factors.py, actions-engine/app/schemas.py, actions-engine/app/service.py, actions-engine/app/router.py, frontend/src/api/actions.js, frontend/src/pages/Dashboard.jsx, frontend/src/App.jsx, api-gateway/app/router.py]

key-decisions:
  - "CO2 factors duplicated in actions-engine service to avoid cross-service imports at runtime"
  - "Survey proxy routes placed before catch-all in gateway to avoid routing conflicts"

patterns-established:
  - "Stepper component pattern for integer cycle selection (0-14)"
  - "Survey prompt/results card pattern on Dashboard"

issues-created: []

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 1, Plan 05: Weekly Appliance Surveys Summary

**Weekly survey for lavatrice/lavastoviglie with per-cycle CO2 factors (EU Energy Label data) and dashboard integration**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T00:00:00Z
- **Completed:** 2026-03-28T00:05:00Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Appliance CO2 emission factors added (washing machine by temp, dishwasher by mode, dryer)
- Weekly survey backend with submit and latest-survey endpoints
- Italian-language survey UI with stepper inputs and temperature/mode selectors
- Dashboard shows survey prompt if not done this week, or results summary if submitted

## Task Commits

Each task was committed atomically:

1. **Task 1: Create weekly survey backend and appliance CO2 factors** - `0350772` (feat)
2. **Task 2: Build weekly survey UI and integrate with dashboard** - `902094e` (feat)

## Files Created/Modified
- `footprint-engine/app/factors.py` - Added WASHING_MACHINE, DISHWASHER, DRYER CO2 per-cycle constants
- `actions-engine/app/schemas.py` - WashingMachineTemp/DishwasherMode enums, WeeklySurveyRequest/Response schemas
- `actions-engine/app/service.py` - calculate_appliance_co2(), build_survey_response(), local CO2 factor dicts
- `actions-engine/app/router.py` - POST/GET weekly-survey endpoints
- `frontend/src/pages/WeeklySurvey.jsx` - Card-based form with lavatrice + lavastoviglie sections
- `frontend/src/hooks/useDashboard.js` - useLatestSurvey() and useSubmitSurvey() hooks
- `frontend/src/api/actions.js` - submitWeeklySurvey() and getLatestSurvey() API functions
- `frontend/src/pages/Dashboard.jsx` - Survey prompt/results card
- `frontend/src/App.jsx` - /weekly-survey route
- `api-gateway/app/router.py` - Proxy routes for weekly-survey endpoints

## Decisions Made
- CO2 factors duplicated locally in actions-engine service to avoid cross-service imports at runtime
- Survey proxy routes placed before the `/{action_id}/complete` catch-all in gateway router to avoid routing conflicts

## Deviations from Plan
None - plan executed exactly as written

## Issues Encountered
None

## Next Phase Readiness
- Weekly survey complete, ready for Plan 06 (Dashboard & Narrative Refresh)
- Scheduler notification for weekly survey reminders not included in this plan (mentioned in roadmap Phase 4 but not in plan tasks)

---
*Phase: 01-green-buddy-ux*
*Completed: 2026-03-28*

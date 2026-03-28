---
phase: 01-green-buddy-ux
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, pydantic, footprint, pets, commute]

requires:
  - phase: none
    provides: existing microservice architecture
provides:
  - commute_days_per_week, has_pets, pet_type, pet_count fields on user profile
  - pet emission factors (dog/cat/small_animal) in footprint engine
  - transport scaling by commute frequency
  - gateway orchestration fetching profile before footprint calculation
affects: [01-green-buddy-ux, frontend-onboarding, dashboard]

tech-stack:
  added: []
  patterns: [gateway profile-fetch before footprint calc]

key-files:
  created: []
  modified:
    - user-profile/app/models.py
    - user-profile/app/schemas.py
    - footprint-engine/app/enums.py
    - footprint-engine/app/factors.py
    - footprint-engine/app/schemas.py
    - footprint-engine/app/service.py
    - api-gateway/app/router.py

key-decisions:
  - "Gateway fetches profile before calling footprint engine to assemble full request"
  - "Pet emission factors from Okin 2017 UCLA study: dog=4.2, cat=2.1, small_animal=0.5 kg CO2/week"
  - "Transport scaled by commute_days_per_week/5.0 ratio"

patterns-established:
  - "Gateway orchestration: fetch profile → enrich → call downstream"

issues-created: []

duration: 8min
completed: 2026-03-28
---

# Phase 1, Plan 01: Enhanced Onboarding Backend Summary

**New profile fields (commute, pets) with personalized footprint calculation using Okin 2017 pet factors and commute-day scaling**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-28
- **Completed:** 2026-03-28
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- User model expanded with commute_days_per_week, has_pets, pet_type, pet_count
- Footprint engine calculates pets_kg and scales transport by commute days
- API gateway now fetches full profile before footprint calculation
- onboarding_complete now requires commute_days_per_week and has_pets

## Task Commits

Each task was committed atomically:

1. **Task 1: Add new profile fields to user-profile service** - `cd3b4b4` (feat)
2. **Task 2: Add pet and commute-frequency emission factors to footprint engine** - `24790f8` (feat)
3. **Task 3: Update API gateway to pass new fields through** - `edee81d` (feat)

## Files Created/Modified
- `user-profile/app/models.py` - Added 4 new columns + updated onboarding_complete
- `user-profile/app/schemas.py` - PetType enum, new fields on request/response schemas
- `footprint-engine/app/enums.py` - PetType enum
- `footprint-engine/app/factors.py` - EMISSION_FACTOR_PET_WEEKLY dict
- `footprint-engine/app/schemas.py` - commute/pet fields on FootprintRequest, pets_kg on CategoryBreakdown
- `footprint-engine/app/service.py` - Commute scaling + pet emission calculation
- `api-gateway/app/router.py` - Profile fetch + enriched footprint request

## Decisions Made
- Gateway fetches profile before calling footprint engine (orchestration pattern) rather than having footprint engine call user-profile directly
- Pet emission factors sourced from Gregory Okin, UCLA 2017 (PLOS ONE)
- Transport assumed km scaled by commute_days_per_week / 5.0 ratio
- onboarding_complete requires commute_days_per_week and has_pets but NOT pet_type/pet_count (not everyone has pets)

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered
None

## Next Phase Readiness
- Backend fields are ready for frontend onboarding UI to consume
- Footprint engine accepts new fields with sensible defaults (commute=5, pets=0)
- No DB migration created — will need one before deployment (SQLite/Postgres)

---
*Phase: 01-green-buddy-ux*
*Completed: 2026-03-28*

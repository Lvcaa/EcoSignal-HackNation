---
phase: 01-green-buddy-ux
plan: 02
subsystem: ui
tags: [react, tailwind, onboarding, vite]

# Dependency graph
requires:
  - phase: 01-green-buddy-ux/01
    provides: backend profile fields (commute_days_per_week, has_pets, pet_type, pet_count) and footprint calculation
provides:
  - 6-step onboarding UI flow (Zip, Transport, Commute, Diet, Home, Pet)
  - Baseline CO2 calculation triggered on onboarding completion
affects: [05-dashboard-narrative]

# Tech tracking
tech-stack:
  added: []
  patterns: [SelectionCard-based step pages, range slider for numeric input, conditional rendering for pet details]

key-files:
  created:
    - frontend/src/pages/onboarding/CommuteStep.jsx
    - frontend/src/pages/onboarding/HomeStep.jsx
    - frontend/src/pages/onboarding/PetStep.jsx
  modified:
    - frontend/src/components/onboarding/OnboardingShell.jsx
    - frontend/src/components/onboarding/ProgressDots.jsx
    - frontend/src/pages/onboarding/DietStep.jsx
    - frontend/src/pages/onboarding/TransportStep.jsx
    - frontend/src/pages/onboarding/ZipStep.jsx
    - frontend/src/App.jsx

key-decisions:
  - "ProgressDots default total changed from 3 to 6"
  - "PetStep is final step, triggers both profile save and footprint calculation"
  - "OnboardingShell handleFinish calls submitOnboarding then calculateFootprint sequentially"

patterns-established:
  - "Conditional step content: PetStep shows pet details only when has_pets=true"
  - "Range slider pattern for numeric values (home_size_sqm)"

issues-created: []

# Metrics
duration: 15min
completed: 2026-03-28
---

# Plan 02: Extended Onboarding Frontend Summary

**6-step onboarding flow with CommuteStep, HomeStep, PetStep and baseline CO2 calculation on completion**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-28
- **Completed:** 2026-03-28
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Created CommuteStep (0-7 day commute frequency with SelectionCards)
- Created HomeStep (apartment/house type + size slider 10-300 m²)
- Created PetStep (yes/no toggle, pet type selector, pet count 1-5)
- Wired 6-step flow: Zip → Transport → Commute → Diet → Home → Pet
- Final step triggers profile save + footprint calculation sequentially
- All UI in Italian matching existing design system

## Task Commits

Each task was committed atomically:

1. **Task 1: Create new onboarding step components** - `db435f7` (feat)
2. **Task 2: Wire new steps into onboarding flow** - `19f1045` (feat)

## Files Created/Modified
- `frontend/src/pages/onboarding/CommuteStep.jsx` - Commute days per week selector (0-7)
- `frontend/src/pages/onboarding/HomeStep.jsx` - Home type + size slider
- `frontend/src/pages/onboarding/PetStep.jsx` - Pet toggle, type, count selector
- `frontend/src/components/onboarding/OnboardingShell.jsx` - Extended state, footprint calc on finish
- `frontend/src/components/onboarding/ProgressDots.jsx` - Default total changed to 6
- `frontend/src/pages/onboarding/DietStep.jsx` - No longer triggers finish, advances to HomeStep
- `frontend/src/pages/onboarding/TransportStep.jsx` - Navigates to CommuteStep
- `frontend/src/pages/onboarding/ZipStep.jsx` - ProgressDots total updated
- `frontend/src/App.jsx` - Added routes for commute, home, pet

## Decisions Made
- ProgressDots default total changed from 3 to 6 (avoids passing total to every step)
- PetStep is the final step and triggers both profile save and footprint calculation
- DietStep converted from finish trigger to intermediate navigation step

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Database schema out of sync**
- **Found during:** Checkpoint verification
- **Issue:** Postgres volume had old schema without new columns from Plan 01-01. `create_all()` doesn't alter existing tables.
- **Fix:** Removed postgres volume and restarted containers to recreate fresh schema
- **Verification:** Register/login endpoints work, all columns present

---

**Total deviations:** 1 auto-fixed (1 blocking), 0 deferred
**Impact on plan:** Fix was necessary for any auth/profile operations to work. Infrastructure issue, no code change needed.

## Issues Encountered
- user-profile service returned 500 on login/register due to stale DB schema missing new columns. Resolved by resetting postgres volume.

## Next Phase Readiness
- Full 6-step onboarding flow works end-to-end
- Baseline CO2 calculated and available on dashboard
- Ready for Phase 2 (Image Analysis Engine) or Phase 3 (Daily Actions Tracking)

---
*Phase: 01-green-buddy-ux*
*Completed: 2026-03-28*

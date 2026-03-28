# Green Buddy - UX Transformation Roadmap

## Milestone 1: Green Buddy UX

### Phase 1: Enhanced Onboarding
**Goal:** Expand registration flow with new profile fields (commute frequency, pets, home details) and trigger baseline CO2 calculation.
- Add new fields to user-profile service (commute_days_per_week, has_pets, pet_type, pet_count)
- Update onboarding UI with new steps (Home details, Pets, Commute frequency)
- Auto-trigger footprint calculation after onboarding completion
- Display baseline CO2 score on dashboard

### Phase 2: Image Analysis Engine
**Goal:** Create a new service that uses Claude Vision API to analyze photos of meals, groceries, and clothing, extracting items and estimating CO2 impact.
- New `image-analyzer` microservice with Claude Vision
- Meal photo analysis → food items → CO2 estimate
- Grocery photo analysis → product list → CO2 estimate
- Clothing photo analysis → material/brand → CO2 estimate
- Research: Yes

### Phase 3: Daily Actions Tracking
**Goal:** Build the day-by-day action logging UI and backend — meal logging, trip notifications, grocery tracking, clothing tracking.
- Meal logging (photo or text description) with CO2 impact
- Trip/travel notification system with transport mode + distance
- Grocery receipt/photo logging
- Clothing purchase logging
- Update actions-engine to handle new action types with CO2 deltas

### Phase 4: Weekly Surveys & Appliance Tracking
**Goal:** Implement weekly questionnaires for laundry/dishwasher usage and aggregate into footprint.
- Weekly survey UI (lavatrice/lavastoviglie frequency, temperature, load size)
- Scheduler-triggered push for weekly surveys
- CO2 calculation for appliance usage
- Integration with footprint engine for running totals

### Phase 5: Dashboard & Narrative Refresh
**Goal:** Redesign dashboard to show current vs baseline CO2, daily action feed, and updated AI narrative.
- Dashboard redesign with current CO2 vs baseline comparison
- Daily action timeline/feed
- Updated AI narrative prompt incorporating daily actions
- Branding update: EcoSignal → Green Buddy throughout

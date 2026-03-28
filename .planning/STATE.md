# Project State

## Current Position
Phase 1 (Enhanced Onboarding) — Plan 05 complete, ready for Plan 06

## Accumulated Decisions
- Existing microservice architecture preserved
- All services async Python/FastAPI
- Claude API used for both narrative and image analysis
- Gateway fetches profile before footprint calculation (orchestration pattern)
- Pet emission factors from Okin 2017: dog=4.2, cat=2.1, small_animal=0.5 kg CO2/week
- Transport scaled by commute_days_per_week / 5.0
- Onboarding flow: Zip → Transport → Commute → Diet → Home → Pet (6 steps)
- ProgressDots default total = 6
- PetStep is final step, triggers profile save then footprint calculation
- create_all() won't alter existing tables — DB volume reset needed after model changes
- Claude Vision API (Anthropic SDK) for image analysis
- Port 8008 for image-analyzer service
- Three analysis types: meal, grocery, clothing with Italian-language prompts
- ActionLog model stores per-action CO2 deltas with flexible JSON metadata
- Trip CO2 calculated locally: car=0.21, transit=0.089, bike=0, walk=0 kg/km
- BottomNav has 5 tabs: Home, Azioni, Community, Progress, Profilo
- Image-analyzer response accessed via analysis.result.total_co2_kg (nested under result)
- Appliance CO2 factors: washing_machine cold=0.3, warm=0.6, hot=1.0, very_hot=1.5; dishwasher eco=0.4, normal=0.7, intensive=1.1; dryer=2.0 kg/cycle
- CO2 factors duplicated in actions-engine service (no cross-service imports)
- Weekly survey stored as ActionLog with type=appliance

## Deferred Issues
None yet

## Blockers
None

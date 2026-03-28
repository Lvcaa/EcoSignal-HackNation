# Green Buddy

**App rebrand from EcoSignal to Green Buddy.**

## Vision
A mobile-first web app that helps Italian users understand and reduce their environmental impact through daily tracking of meals, travel, groceries, clothing, and appliance usage — combining photo AI analysis with CO2 calculation.

## Architecture
- Microservices (FastAPI, async Python)
- PostgreSQL 16 + Redis 7
- React 18 + Vite + TailwindCSS frontend
- Claude API for AI narrative + image analysis
- Docker Compose orchestration

## Core Flow
1. User registers with lifestyle profile (commute frequency, diet, location, pets)
2. Footprint engine calculates baseline CO2 score
3. Day-by-day: user logs actions (meal photos, trip notifications, grocery photos, clothing photos, weekly appliance surveys)
4. Each action adjusts the user's current CO2 footprint
5. AI provides narrative feedback connecting habits to environmental impact

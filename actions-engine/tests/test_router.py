"""HTTP integration tests for actions-engine router."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from httpx import AsyncClient

from app.repository import ActionRepository
from tests.conftest import seed_completion

ROME_TZ = ZoneInfo("Europe/Rome")


class TestGetActions:
    async def test_no_user_id_returns_422(self, client: AsyncClient) -> None:
        resp = await client.get("/actions")
        assert resp.status_code == 422

    async def test_valid_user_returns_3_suggestions(
        self, client: AsyncClient, valid_user_id: uuid.UUID
    ) -> None:
        resp = await client.get("/actions", params={"user_id": str(valid_user_id)})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert all("action_id" in item for item in data)

    async def test_category_filter_transport(
        self, client: AsyncClient, valid_user_id: uuid.UUID
    ) -> None:
        resp = await client.get(
            "/actions", params={"user_id": str(valid_user_id), "category": "transport"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["category"] == "transport" for item in data)

    async def test_completed_today_flag(
        self,
        client: AsyncClient,
        valid_user_id: uuid.UUID,
        action_repository: ActionRepository,
    ) -> None:
        # Complete all transport actions today
        today = date.today()
        for aid in ["transport_01", "transport_02", "transport_03", "transport_04"]:
            await seed_completion(action_repository, valid_user_id, aid, today)

        resp = await client.get(
            "/actions", params={"user_id": str(valid_user_id), "category": "transport"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["completed_today"] for item in data)


class TestCompleteAction:
    async def test_valid_completion(
        self, client: AsyncClient, valid_user_id: uuid.UUID
    ) -> None:
        resp = await client.post(
            "/actions/transport_01/complete",
            json={"user_id": str(valid_user_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_id"] == "transport_01"
        assert data["streak_days"] == 1

    async def test_streak_increments_after_yesterday(
        self,
        client: AsyncClient,
        valid_user_id: uuid.UUID,
        action_repository: ActionRepository,
    ) -> None:
        yesterday = date.today() - timedelta(days=1)
        await seed_completion(action_repository, valid_user_id, "food_01", yesterday)
        # Update streak to reflect yesterday's completion
        await action_repository.update_streak(valid_user_id, 1, yesterday, increment_total=False)
        await action_repository.session.commit()

        resp = await client.post(
            "/actions/transport_01/complete",
            json={"user_id": str(valid_user_id)},
        )
        assert resp.status_code == 200
        assert resp.json()["streak_days"] == 2

    async def test_unknown_action_returns_404(
        self, client: AsyncClient, valid_user_id: uuid.UUID
    ) -> None:
        resp = await client.post(
            "/actions/nonexistent_99/complete",
            json={"user_id": str(valid_user_id)},
        )
        assert resp.status_code == 404

    async def test_missing_user_id_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/actions/transport_01/complete", json={})
        assert resp.status_code == 422

    async def test_idempotent_same_day(
        self, client: AsyncClient, valid_user_id: uuid.UUID
    ) -> None:
        payload = {"user_id": str(valid_user_id)}
        resp1 = await client.post("/actions/transport_01/complete", json=payload)
        resp2 = await client.post("/actions/transport_01/complete", json=payload)
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["streak_days"] == resp2.json()["streak_days"]


class TestGetStreak:
    async def test_no_completions(
        self, client: AsyncClient, valid_user_id: uuid.UUID
    ) -> None:
        resp = await client.get("/actions/streak", params={"user_id": str(valid_user_id)})
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_streak"] == 0
        assert data["total_completions"] == 0

    async def test_after_one_completion(
        self, client: AsyncClient, valid_user_id: uuid.UUID
    ) -> None:
        await client.post(
            "/actions/transport_01/complete",
            json={"user_id": str(valid_user_id)},
        )
        resp = await client.get("/actions/streak", params={"user_id": str(valid_user_id)})
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_streak"] == 1
        assert data["total_completions"] == 1

    async def test_no_user_id_returns_422(self, client: AsyncClient) -> None:
        resp = await client.get("/actions/streak")
        assert resp.status_code == 422


class TestHealth:
    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "version": "1.0.0"}

"""HTTP-layer tests for env-data router endpoints."""

from __future__ import annotations

import re

from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from tests.conftest import (
    MOCK_ARCHIVE_RESPONSE,
    MOCK_FORECAST_RESPONSE,
    MOCK_OPENAQ_RESPONSE,
)


def _register_all(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=re.compile(r".*/locations.*"), json=MOCK_OPENAQ_RESPONSE)
    httpx_mock.add_response(url=re.compile(r".*/forecast.*"), json=MOCK_FORECAST_RESPONSE)
    httpx_mock.add_response(url=re.compile(r".*/archive.*"), json=MOCK_ARCHIVE_RESPONSE)


class TestCombinedEndpoint:
    async def test_success(self, client: AsyncClient, httpx_mock: HTTPXMock) -> None:
        _register_all(httpx_mock)
        resp = await client.get("/api/v1/env/combined", params={"zip_code": "00100"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["zip_code"] == "00100"
        assert "air_quality" in body
        assert "climate" in body

    async def test_unknown_zip_404(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/env/combined", params={"zip_code": "99999"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "ZIP code not supported"

    async def test_missing_param_422(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/env/combined")
        assert resp.status_code == 422


class TestAirQualityEndpoint:
    async def test_success(self, client: AsyncClient, httpx_mock: HTTPXMock) -> None:
        _register_all(httpx_mock)
        resp = await client.get("/api/v1/env/air-quality", params={"zip_code": "20100"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["zip_code"] == "20100"
        assert "pm25" in body


class TestClimateContextEndpoint:
    async def test_success(self, client: AsyncClient, httpx_mock: HTTPXMock) -> None:
        _register_all(httpx_mock)
        resp = await client.get("/api/v1/env/climate-context", params={"zip_code": "40100"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["zip_code"] == "40100"
        assert "current_temp_c" in body


class TestCacheHitScenario:
    async def test_second_request_uses_cache(
        self,
        client: AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        _register_all(httpx_mock)

        # First request — cache miss, hits APIs
        resp1 = await client.get("/api/v1/env/combined", params={"zip_code": "00100"})
        assert resp1.status_code == 200

        # Second request — should use cache, no new HTTP calls
        resp2 = await client.get("/api/v1/env/combined", params={"zip_code": "00100"})
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["air_quality"]["source"] == "cache"
        assert body["climate"]["source"] == "cache"


class TestFallbackScenario:
    async def test_openaq_timeout_returns_fallback(
        self, client: AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(url=re.compile(r".*/locations.*"), status_code=500)
        httpx_mock.add_response(url=re.compile(r".*/forecast.*"), json=MOCK_FORECAST_RESPONSE)
        httpx_mock.add_response(url=re.compile(r".*/archive.*"), json=MOCK_ARCHIVE_RESPONSE)

        resp = await client.get("/api/v1/env/combined", params={"zip_code": "00100"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["air_quality"]["is_fallback"] is True
        assert body["climate"]["is_fallback"] is False


class TestHealth:
    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "version": "1.0.0"}

"""Climatiq API client with in-memory cache and fallback support."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.climatiq.io"
ENERGY_URL = f"{BASE_URL}/energy/v1.3"
ESTIMATE_URL = f"{BASE_URL}/data/v1/estimate"
BATCH_URL = f"{BASE_URL}/data/v1/estimate/batch"

CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 days
REQUEST_TIMEOUT = 10.0  # seconds


class ClimatiqClient:
    """Thin async wrapper around the Climatiq REST API with TTL cache."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._cache: dict[str, tuple[float, float]] = {}  # key -> (co2e_kg, expiry)
        self._enabled = bool(api_key)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _cache_key(self, activity_id: str, params: dict[str, Any]) -> str:
        sorted_params = sorted(params.items())
        return f"{activity_id}:{sorted_params}"

    def _get_cached(self, key: str) -> float | None:
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            del self._cache[key]
        return None

    def _set_cached(self, key: str, value: float) -> None:
        self._cache[key] = (value, time.time() + CACHE_TTL_SECONDS)

    async def estimate(
        self,
        activity_id: str,
        parameters: dict[str, Any],
        region: str = "IT",
        data_version: str = "^21",
        fallback: float | None = None,
    ) -> float:
        """Estimate CO2e for a single activity. Returns kg CO2e.

        Falls back to `fallback` value on any error.
        """
        cache_key = self._cache_key(activity_id, {**parameters, "region": region})
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        if not self._enabled:
            if fallback is not None:
                return fallback
            raise RuntimeError("Climatiq API key not configured and no fallback")

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(
                    ESTIMATE_URL,
                    headers=self._headers(),
                    json={
                        "emission_factor": {
                            "activity_id": activity_id,
                            "region": region,
                            "data_version": data_version,
                        },
                        "parameters": parameters,
                    },
                )
                resp.raise_for_status()
                co2e = resp.json()["co2e"]
                self._set_cached(cache_key, co2e)
                logger.info(
                    "Climatiq estimate: %s -> %.4f kg CO2e", activity_id, co2e
                )
                return co2e
        except Exception:
            logger.warning(
                "Climatiq estimate failed for %s, using fallback=%.4f",
                activity_id,
                fallback or 0.0,
                exc_info=True,
            )
            if fallback is not None:
                return fallback
            raise

    async def estimate_electricity(
        self,
        energy_kwh: float,
        region: str = "IT",
        fallback: float | None = None,
    ) -> float:
        """Estimate CO2e for electricity consumption. Returns kg CO2e."""
        cache_key = f"electricity:{region}:{energy_kwh}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        if not self._enabled:
            if fallback is not None:
                return fallback
            raise RuntimeError("Climatiq API key not configured and no fallback")

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(
                    f"{ENERGY_URL}/electricity",
                    headers=self._headers(),
                    json={
                        "region": region,
                        "amount": {
                            "energy": energy_kwh,
                            "energy_unit": "kWh",
                        },
                    },
                )
                resp.raise_for_status()
                co2e = resp.json()["co2e"]
                self._set_cached(cache_key, co2e)
                logger.info(
                    "Climatiq electricity: %.1f kWh in %s -> %.4f kg CO2e",
                    energy_kwh,
                    region,
                    co2e,
                )
                return co2e
        except Exception:
            logger.warning(
                "Climatiq electricity failed, using fallback=%.4f",
                fallback or 0.0,
                exc_info=True,
            )
            if fallback is not None:
                return fallback
            raise

    async def batch_estimate(
        self,
        items: list[dict[str, Any]],
        fallbacks: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Batch estimate up to 100 activities. Returns {activity_id: co2e_kg}.

        Each item: {"activity_id": str, "parameters": dict, "region": str}
        """
        if not self._enabled:
            return fallbacks or {}

        fallbacks = fallbacks or {}
        results: dict[str, float] = {}

        # Check cache first, collect uncached
        uncached = []
        for item in items:
            aid = item["activity_id"]
            params = item.get("parameters", {})
            region = item.get("region", "IT")
            cache_key = self._cache_key(aid, {**params, "region": region})
            cached = self._get_cached(cache_key)
            if cached is not None:
                results[aid] = cached
            else:
                uncached.append(item)

        if not uncached:
            return results

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT * 3) as client:
                resp = await client.post(
                    BATCH_URL,
                    headers=self._headers(),
                    json=[
                        {
                            "emission_factor": {
                                "activity_id": item["activity_id"],
                                "region": item.get("region", "IT"),
                                "data_version": item.get("data_version", "^21"),
                            },
                            "parameters": item.get("parameters", {}),
                        }
                        for item in uncached
                    ],
                )
                resp.raise_for_status()
                data = resp.json()

                for item, result in zip(uncached, data.get("results", [])):
                    aid = item["activity_id"]
                    co2e = result.get("co2e", 0.0)
                    params = item.get("parameters", {})
                    region = item.get("region", "IT")
                    cache_key = self._cache_key(aid, {**params, "region": region})
                    self._set_cached(cache_key, co2e)
                    results[aid] = co2e

                logger.info("Climatiq batch: fetched %d factors", len(uncached))
        except Exception:
            logger.warning("Climatiq batch failed, using fallbacks", exc_info=True)

        # Fill missing with fallbacks
        for item in items:
            aid = item["activity_id"]
            if aid not in results:
                results[aid] = fallbacks.get(aid, 0.0)

        return results

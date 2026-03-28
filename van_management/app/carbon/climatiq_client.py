from typing import Any

import httpx

from app.core.config import settings


class CarbonProviderError(RuntimeError):
    pass


class CarbonProviderConfigurationError(CarbonProviderError):
    pass


class CarbonProviderUnavailableError(CarbonProviderError):
    pass


class ClimatiqClient:
    def __init__(self) -> None:
        self.base_url = settings.CLIMATIQ_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(settings.CLIMATIQ_TIMEOUT_SECONDS)

    def estimate(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post_json("/data/v1/estimate", payload)

    def estimate_batch(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        response = self._post_json("/data/v1/estimate/batch", payload)
        if not isinstance(response, list):
            raise CarbonProviderUnavailableError(
                "Unexpected Climatiq batch response format"
            )
        return response

    def _post_json(self, path: str, payload: dict[str, Any] | list[dict[str, Any]]) -> Any:
        if not settings.CLIMATIQ_API_KEY:
            raise CarbonProviderConfigurationError(
                "Carbon provider is not configured: set CLIMATIQ_API_KEY"
            )

        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {settings.CLIMATIQ_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise CarbonProviderUnavailableError(
                f"Climatiq request failed: {exc}"
            ) from exc

        if response.status_code >= 400:
            detail = response.text.strip() or "unknown provider error"
            raise CarbonProviderUnavailableError(
                f"Climatiq returned HTTP {response.status_code}: {detail}"
            )

        return response.json()


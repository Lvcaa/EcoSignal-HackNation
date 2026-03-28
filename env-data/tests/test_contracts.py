"""TASK-21: Contract tests against real OpenAQ v3 and Open-Meteo API schemas.

These tests verify that adapter parsing logic correctly handles real API
response shapes. Payloads exactly match documented API schemas — not
simplified mocks. They are the early-warning system for API drift.
"""

from __future__ import annotations

import re
import statistics

from pytest_httpx import HTTPXMock

from app.adapters import fetch_air_quality, fetch_climate_context
from app.config import Settings
from app.schemas import AQILabel, DataSource, ZipLocation
from app.service import derive_aqi_label

_SETTINGS = Settings(openaq_api_key="test-key")  # type: ignore[call-arg]

_LOCATION = ZipLocation(
    zip_code="00100",
    city="Roma",
    region="Lazio",
    latitude=41.9028,
    longitude=12.4964,
    arpa_region="ARPA_LAZIO",
)

# ===========================================================================
# OpenAQ v3 realistic payloads
# ===========================================================================

OPENAQ_LOCATIONS_RESPONSE: dict = {
    "meta": {
        "name": "openaq-api",
        "website": "/",
        "page": 1,
        "limit": 1,
        "found": 1,
    },
    "results": [
        {
            "id": 12345,
            "name": "Roma - Via Tiburtina",
            "locality": "Roma",
            "timezone": "Europe/Rome",
            "country": {"id": 105, "code": "IT", "name": "Italy"},
            "owner": {"id": 4, "name": "ARPA Lazio"},
            "provider": {"id": 42, "name": "ARPA"},
            "isMobile": False,
            "isMonitor": True,
            "instruments": [{"id": 1, "name": "Government Monitor"}],
            "sensors": [
                {
                    "id": 98001,
                    "name": "pm25 \u00b5g/m\u00b3",
                    "parameter": {
                        "id": 2,
                        "name": "pm25",
                        "units": "\u00b5g/m\u00b3",
                        "displayName": "PM2.5",
                    },
                    "latest": {
                        "datetime": "2026-03-28T10:00:00Z",
                        "value": 18.5,
                        "coordinates": {"latitude": 41.89, "longitude": 12.51},
                    },
                },
                {
                    "id": 98002,
                    "name": "pm10 \u00b5g/m\u00b3",
                    "parameter": {
                        "id": 1,
                        "name": "pm10",
                        "units": "\u00b5g/m\u00b3",
                        "displayName": "PM10",
                    },
                    "latest": {
                        "datetime": "2026-03-28T10:00:00Z",
                        "value": 32.0,
                        "coordinates": {"latitude": 41.89, "longitude": 12.51},
                    },
                },
            ],
            "coordinates": {"latitude": 41.8902, "longitude": 12.4924},
            "bounds": [12.49, 41.89, 12.50, 41.90],
            "distance": 1234.5,
            "datetimeFirst": "2020-01-01T00:00:00Z",
            "datetimeLast": "2026-03-28T10:00:00Z",
        }
    ],
}

OPENAQ_EMPTY_RESPONSE: dict = {
    "meta": {
        "name": "openaq-api",
        "website": "/",
        "page": 1,
        "limit": 1,
        "found": 0,
    },
    "results": [],
}

# ===========================================================================
# Open-Meteo realistic payloads
# ===========================================================================

OPEN_METEO_FORECAST_RESPONSE: dict = {
    "latitude": 41.9,
    "longitude": 12.5,
    "generationtime_ms": 0.123,
    "utc_offset_seconds": 3600,
    "timezone": "Europe/Rome",
    "timezone_abbreviation": "CET",
    "elevation": 20.0,
    "current_units": {
        "time": "iso8601",
        "interval": "seconds",
        "temperature_2m": "\u00b0C",
    },
    "current": {
        "time": "2026-03-28T12:00",
        "interval": 900,
        "temperature_2m": 22.3,
    },
}

OPEN_METEO_ARCHIVE_RESPONSE: dict = {
    "latitude": 41.9,
    "longitude": 12.5,
    "generationtime_ms": 12.5,
    "utc_offset_seconds": 3600,
    "timezone": "Europe/Rome",
    "timezone_abbreviation": "CET",
    "elevation": 20.0,
    "daily_units": {"time": "iso8601", "temperature_2m_mean": "\u00b0C"},
    "daily": {
        "time": [
            "2016-03-01",
            "2016-03-02",
            "2016-03-03",
            "2017-03-01",
            "2017-03-02",
            "2017-03-03",
            "2018-03-01",
            "2018-03-02",
        ],
        "temperature_2m_mean": [18.1, 19.2, 17.8, 20.1, 18.9, 19.5, 21.0, None],
    },
}


# ===========================================================================
# OpenAQ contract tests
# ===========================================================================


class TestOpenAQFullPayload:
    """Parse OPENAQ_LOCATIONS_RESPONSE through the real adapter."""

    async def test_station_id(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_LOCATIONS_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.station_id == "12345"

    async def test_station_name(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_LOCATIONS_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.station_name == "Roma - Via Tiburtina"

    async def test_pm25_value(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_LOCATIONS_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.pm25 == 18.5

    async def test_pm10_value(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_LOCATIONS_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.pm10 == 32.0

    async def test_aqi_label_moderate(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_LOCATIONS_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        # 18.5 is in 15-35 range → moderate
        assert result.aqi_label == AQILabel.MODERATE

    async def test_is_fallback_false(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_LOCATIONS_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.is_fallback is False

    async def test_source_openaq(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_LOCATIONS_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.source == DataSource.OPENAQ


class TestOpenAQEmptyResponse:
    """Parse OPENAQ_EMPTY_RESPONSE — no stations found."""

    async def test_is_fallback_true(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_EMPTY_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.is_fallback is True

    async def test_default_aqi_moderate(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_EMPTY_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.aqi_label == AQILabel.MODERATE

    async def test_pm25_none(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_EMPTY_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.pm25 is None

    async def test_pm10_none(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=OPENAQ_EMPTY_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)
        assert result.pm10 is None


class TestOpenAQPartialSensors:
    """Only PM10 sensor present — no PM2.5."""

    async def test_pm25_none_pm10_present(self, httpx_mock: HTTPXMock) -> None:
        payload = {
            "meta": OPENAQ_LOCATIONS_RESPONSE["meta"],
            "results": [
                {
                    **OPENAQ_LOCATIONS_RESPONSE["results"][0],
                    "sensors": [
                        {
                            "id": 98002,
                            "name": "pm10 \u00b5g/m\u00b3",
                            "parameter": {
                                "id": 1,
                                "name": "pm10",
                                "units": "\u00b5g/m\u00b3",
                                "displayName": "PM10",
                            },
                            "latest": {
                                "datetime": "2026-03-28T10:00:00Z",
                                "value": 32.0,
                                "coordinates": {
                                    "latitude": 41.89,
                                    "longitude": 12.51,
                                },
                            },
                        }
                    ],
                }
            ],
        }
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=payload
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)

        assert result.pm25 is None
        assert result.pm10 == 32.0
        # aqi derived from pm10 * 0.6 = 19.2 → moderate
        assert result.aqi_label == derive_aqi_label(None, 32.0)

    async def test_o3_sensor_present(self, httpx_mock: HTTPXMock) -> None:
        payload = {
            "meta": OPENAQ_LOCATIONS_RESPONSE["meta"],
            "results": [
                {
                    **OPENAQ_LOCATIONS_RESPONSE["results"][0],
                    "sensors": [
                        *OPENAQ_LOCATIONS_RESPONSE["results"][0]["sensors"],
                        {
                            "id": 98003,
                            "name": "o3 \u00b5g/m\u00b3",
                            "parameter": {
                                "id": 3,
                                "name": "o3",
                                "units": "\u00b5g/m\u00b3",
                                "displayName": "O3",
                            },
                            "latest": {
                                "datetime": "2026-03-28T10:00:00Z",
                                "value": 85.0,
                                "coordinates": {
                                    "latitude": 41.89,
                                    "longitude": 12.51,
                                },
                            },
                        },
                    ],
                }
            ],
        }
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=payload
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)

        assert result.o3 == 85.0


# ===========================================================================
# Open-Meteo contract tests
# ===========================================================================


class TestOpenMeteoFullPayload:
    """Parse forecast + archive through the real adapter."""

    async def test_current_temp(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        assert result.current_temp_c == 22.3

    async def test_historical_avg(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        valid_temps = [18.1, 19.2, 17.8, 20.1, 18.9, 19.5, 21.0]
        expected_avg = round(statistics.mean(valid_temps), 2)  # 19.23
        assert result.anomaly_c is not None
        actual_avg = round(result.current_temp_c - result.anomaly_c, 2)  # type: ignore[operator]
        assert actual_avg == expected_avg

    async def test_anomaly_value(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        valid_temps = [18.1, 19.2, 17.8, 20.1, 18.9, 19.5, 21.0]
        expected_anomaly = round(22.3 - statistics.mean(valid_temps), 2)
        assert result.anomaly_c == expected_anomaly

    async def test_anomaly_label_above(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        assert result.anomaly_label is not None
        assert "above" in result.anomaly_label
        valid = [18.1, 19.2, 17.8, 20.1, 18.9, 19.5, 21.0]
        expected_anomaly = round(22.3 - statistics.mean(valid), 2)
        assert str(expected_anomaly) in result.anomaly_label

    async def test_is_fallback_false(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        assert result.is_fallback is False

    async def test_source_open_meteo(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        assert result.source == DataSource.OPEN_METEO


class TestOpenMeteoNoneFiltering:
    """None values in archive are filtered before averaging."""

    async def test_none_excluded_from_average(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        # 7 valid temps out of 8 (one None)
        valid_temps = [18.1, 19.2, 17.8, 20.1, 18.9, 19.5, 21.0]
        expected_avg = statistics.mean(valid_temps)
        expected_anomaly = round(22.3 - expected_avg, 2)
        assert result.anomaly_c == expected_anomaly


class TestOpenMeteoAllNone:
    """All archive temps are None — fallback behavior."""

    async def test_all_none_returns_fallback(self, httpx_mock: HTTPXMock) -> None:
        all_none_archive: dict = {
            **OPEN_METEO_ARCHIVE_RESPONSE,
            "daily": {
                "time": ["2016-03-01", "2016-03-02"],
                "temperature_2m_mean": [None, None],
            },
        }
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=all_none_archive
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        # No historical avg means no anomaly
        assert result.anomaly_c is None
        assert result.anomaly_label is None
        assert result.current_temp_c == 22.3


class TestOpenMeteoBelowAvg:
    """Current temp below historical average."""

    async def test_negative_anomaly(self, httpx_mock: HTTPXMock) -> None:
        cold_forecast: dict = {
            **OPEN_METEO_FORECAST_RESPONSE,
            "current": {"time": "2026-03-28T12:00", "interval": 900, "temperature_2m": 15.0},
        }
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=cold_forecast
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        assert result.anomaly_c is not None
        assert result.anomaly_c < 0
        assert result.anomaly_label is not None
        assert "below" in result.anomaly_label


# ===========================================================================
# Schema drift detection
# ===========================================================================


class TestSchemaDrift:
    """Assert adapters read from documented field paths, not invented ones."""

    async def test_openaq_reads_pm25_from_sensors_latest_value(
        self, httpx_mock: HTTPXMock
    ) -> None:
        """PM2.5 comes from result.sensors[n].latest.value where
        result.sensors[n].parameter.name == 'pm25'."""
        # If we put pm25 at top level but NOT in sensors, adapter should NOT find it
        bad_payload: dict = {
            "meta": OPENAQ_LOCATIONS_RESPONSE["meta"],
            "results": [
                {
                    **OPENAQ_LOCATIONS_RESPONSE["results"][0],
                    "pm25": 999.0,  # Wrong location — not in real API
                    "sensors": [],  # No sensors
                }
            ],
        }
        httpx_mock.add_response(
            url=re.compile(r".*/locations.*"), json=bad_payload
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_air_quality(client, _LOCATION, _SETTINGS)

        # Adapter should NOT read the top-level "pm25" key
        assert result.pm25 is None

    async def test_openmeteo_reads_current_temp_from_nested_path(
        self, httpx_mock: HTTPXMock
    ) -> None:
        """Current temp comes from response.current.temperature_2m,
        NOT response.temperature_2m."""
        bad_payload: dict = {
            **OPEN_METEO_FORECAST_RESPONSE,
            "temperature_2m": 999.0,  # Wrong location
            "current": {"time": "2026-03-28T12:00", "interval": 900, "temperature_2m": 22.3},
        }
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=bad_payload
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=OPEN_METEO_ARCHIVE_RESPONSE
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        assert result.current_temp_c == 22.3  # from current.temperature_2m, not top-level

    async def test_openmeteo_reads_archive_from_daily_nested(
        self, httpx_mock: HTTPXMock
    ) -> None:
        """Archive temps come from response.daily.temperature_2m_mean,
        NOT response.temperature_2m_mean."""
        bad_payload: dict = {
            **OPEN_METEO_ARCHIVE_RESPONSE,
            "temperature_2m_mean": [99.0, 99.0],  # Wrong location
            "daily": {
                "time": ["2016-03-01"],
                "temperature_2m_mean": [19.0],
            },
        }
        httpx_mock.add_response(
            url=re.compile(r".*/forecast.*"), json=OPEN_METEO_FORECAST_RESPONSE
        )
        httpx_mock.add_response(
            url=re.compile(r".*/archive.*"), json=bad_payload
        )
        import httpx as httpx_lib

        async with httpx_lib.AsyncClient() as client:
            result = await fetch_climate_context(client, _LOCATION, _SETTINGS)

        # Should use daily.temperature_2m_mean=[19.0], not top-level [99.0, 99.0]
        expected_anomaly = round(22.3 - 19.0, 2)
        assert result.anomaly_c == expected_anomaly

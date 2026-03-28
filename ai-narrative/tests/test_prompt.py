"""Prompt regression tests — TASK-27 coverage."""

from __future__ import annotations

from app.prompt import SYSTEM_PROMPT, build_user_message
from tests.conftest import valid_request


class TestBuildUserMessage:
    """Tests for build_user_message output content."""

    def test_contains_city(self) -> None:
        msg = build_user_message(valid_request())
        assert "Roma" in msg

    def test_contains_zip_code(self) -> None:
        msg = build_user_message(valid_request())
        assert "00100" in msg

    def test_contains_total_co2(self) -> None:
        msg = build_user_message(valid_request())
        assert "76.6" in msg

    def test_contains_italian_transport_label(self) -> None:
        msg = build_user_message(valid_request(transport_mode="car"))
        assert "auto" in msg

    def test_contains_italian_diet_label(self) -> None:
        msg = build_user_message(valid_request(diet_type="meat_weekly"))
        assert "con carne qualche volta a settimana" in msg

    def test_contains_pm25_when_not_fallback(self) -> None:
        msg = build_user_message(valid_request(air_is_fallback=False))
        assert "18.5" in msg

    def test_contains_dati_non_disponibili_air_fallback(self) -> None:
        msg = build_user_message(valid_request(air_is_fallback=True))
        assert "dati non disponibili" in msg

    def test_contains_anomaly_when_not_fallback(self) -> None:
        msg = build_user_message(valid_request(climate_is_fallback=False))
        assert "+2.1°C above historical average" in msg

    def test_contains_dati_non_disponibili_climate_fallback(self) -> None:
        msg = build_user_message(valid_request(climate_is_fallback=True))
        assert "dati non disponibili" in msg

    def test_output_is_nonempty_string(self) -> None:
        msg = build_user_message(valid_request())
        assert isinstance(msg, str)
        assert len(msg) > 0


class TestSystemPrompt:
    """Tests for SYSTEM_PROMPT content."""

    def test_contains_italian_instruction(self) -> None:
        assert "Italian" in SYSTEM_PROMPT or "italiano" in SYSTEM_PROMPT

    def test_contains_json_instruction(self) -> None:
        assert "JSON" in SYSTEM_PROMPT

    def test_contains_required_keys(self) -> None:
        for key in ("headline", "body", "local_context", "source_note"):
            assert key in SYSTEM_PROMPT

    def test_no_placeholder_text(self) -> None:
        assert "{user_id}" not in SYSTEM_PROMPT

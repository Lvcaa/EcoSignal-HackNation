from math import isclose

from app.core.config import settings


FACTOR_BY_ACTIVITY_ID = {
    "electricity-supply_grid-source_total_supplier_mix": 0.4,
    "water_supply-type_na": 0.3,
    "passenger_vehicle-vehicle_type_medium_car-fuel_source_petrol-engine_size_gt_1.6l_lt_2l-vehicle_age_na-vehicle_weight_gt_950kg_lt_1350kg": 0.2,
    "passenger_vehicle-vehicle_type_medium_car-fuel_source_diesel-engine_size_gt_1.8l_lt_2.2l-vehicle_age_na-vehicle_weight_gt_1050kg_lt_1450kg": 0.18,
    "passenger_vehicle-vehicle_type_local_bus_not_london-fuel_source_na-distance_na-engine_size_na": 0.1,
    "passenger_train-route_type_na-fuel_source_na": 0.03,
    "food-type_beef": 12.0,
    "food-type_chicken_breast_flesh_and_skin_raw": 5.0,
    "consumer_goods-type_milk": 1.2,
    "waste_management-type_plastic_mixed_recycled_treatment_of_waste_polyethylene_recycling-disposal_method_recycling": 0.05,
    "commercial_vehicle-vehicle_type_truck_light-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na": 0.5,
}


def _fake_activity_data(parameters: dict) -> tuple[float, str]:
    if "passengers" in parameters:
        return parameters["passengers"] * parameters["distance"], "passenger-km"
    if "distance" in parameters:
        return parameters["distance"], parameters.get("distance_unit", "km")
    if "energy" in parameters:
        return parameters["energy"], parameters.get("energy_unit", "kWh")
    if "volume" in parameters:
        return parameters["volume"], parameters.get("volume_unit", "m3")
    if "weight" in parameters:
        return parameters["weight"], parameters.get("weight_unit", "kg")
    raise AssertionError(f"Unsupported parameters payload: {parameters}")


def _fake_estimate_response(payload: dict) -> dict:
    selector = payload["emission_factor"]
    activity_id = selector["activity_id"]
    factor = FACTOR_BY_ACTIVITY_ID[activity_id]
    activity_value, activity_unit = _fake_activity_data(payload["parameters"])
    co2e = round(activity_value * factor, 6)
    return {
        "co2e": co2e,
        "co2e_unit": "kg",
        "emission_factor": {
            "id": f"fake-{abs(hash(activity_id))}",
            "activity_id": activity_id,
            "source": selector.get("source", "TestSource"),
            "year": selector.get("year"),
            "region": selector.get("region"),
            "source_lca_activity": selector.get("source_lca_activity"),
            "data_version": selector.get("data_version"),
            "name": activity_id,
        },
        "activity_data": {
            "activity_value": activity_value,
            "activity_unit": activity_unit,
        },
        "audit_trail": "selector",
    }


def fake_estimate(self, payload: dict) -> dict:  # noqa: ARG001
    return _fake_estimate_response(payload)


def fake_estimate_batch(self, payload: list[dict]) -> list[dict]:  # noqa: ARG001
    return [_fake_estimate_response(item) for item in payload]


def test_carbon_evaluate_success(client, monkeypatch):
    monkeypatch.setattr(settings, "CLIMATIQ_API_KEY", "test-key")
    monkeypatch.setattr("app.carbon.climatiq_client.ClimatiqClient.estimate", fake_estimate)

    resp = client.post(
        "/api/v1/carbon/evaluate",
        json={
            "activity_type": "household_electricity",
            "quantity": 5,
            "unit": "kWh",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["scope"] == "personal"
    assert body["data"]["co2e_kg"] == 2.0
    assert body["data"]["activity_type"] == "household_electricity"
    assert body["data"]["provider_data_version"] == settings.CLIMATIQ_DATA_VERSION


def test_carbon_evaluate_batch_success(client, monkeypatch):
    monkeypatch.setattr(settings, "CLIMATIQ_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.carbon.climatiq_client.ClimatiqClient.estimate_batch", fake_estimate_batch
    )

    resp = client.post(
        "/api/v1/carbon/evaluate/batch",
        json={
            "evaluations": [
                {
                    "activity_type": "household_electricity",
                    "quantity": 5,
                    "unit": "kWh",
                },
                {
                    "activity_type": "public_bus",
                    "quantity": 10,
                    "unit": "passenger_km",
                },
            ]
        },
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["accepted"] == 2
    assert data["total_co2e_kg"] == 3.0
    assert len(data["results"]) == 2


def test_personal_daily_footprint_success(client, monkeypatch):
    monkeypatch.setattr(settings, "CLIMATIQ_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.carbon.climatiq_client.ClimatiqClient.estimate_batch", fake_estimate_batch
    )

    resp = client.post(
        "/api/v1/carbon/personal/evaluate",
        json={
            "person_id": "USER_001",
            "date": "2026-03-28",
            "transport": [
                {"mode": "car_petrol", "distance_km": 20, "occupancy": 2},
                {"mode": "bus", "distance_km": 10},
            ],
            "food": [
                {"food_category": "beef", "quantity": 0.25, "unit": "kg"},
            ],
            "utilities": [
                {"activity_type": "household_electricity", "quantity": 5, "unit": "kWh"},
            ],
            "waste": [
                {"waste_type": "plastic", "treatment": "recycled", "quantity": 1, "unit": "kg"},
            ],
        },
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isclose(data["category_totals"]["transport"], 3.0, rel_tol=0, abs_tol=1e-6)
    assert isclose(data["category_totals"]["food"], 3.0, rel_tol=0, abs_tol=1e-6)
    assert isclose(data["category_totals"]["utilities"], 2.0, rel_tol=0, abs_tol=1e-6)
    assert isclose(data["category_totals"]["waste"], 0.05, rel_tol=0, abs_tol=1e-6)
    assert isclose(data["total_co2e_kg"], 8.05, rel_tol=0, abs_tol=1e-6)
    assert data["scope"] == "personal"
    assert all(item["evaluation"]["scope"] == "personal" for item in data["items"])
    assert len(data["items"]) == 5


def test_personal_daily_footprint_supports_habit_templates(client, monkeypatch):
    monkeypatch.setattr(settings, "CLIMATIQ_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.carbon.climatiq_client.ClimatiqClient.estimate_batch", fake_estimate_batch
    )

    resp = client.post(
        "/api/v1/carbon/personal/evaluate",
        json={
            "person_id": "USER_002",
            "date": "2026-03-28",
            "habits": [
                {"habit_type": "shower", "count": 2},
                {"habit_type": "washing_machine", "count": 1},
            ],
        },
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["scope"] == "personal"
    assert isclose(data["category_totals"]["utilities"], 2.031, rel_tol=0, abs_tol=1e-6)
    assert isclose(data["total_co2e_kg"], 2.031, rel_tol=0, abs_tol=1e-6)
    assert len(data["items"]) == 4
    assert all(item["source_type"] == "habit" for item in data["items"])
    assert {item["source_key"] for item in data["items"]} == {"shower", "washing_machine"}


def test_personal_car_requires_occupancy(client):
    resp = client.post(
        "/api/v1/carbon/personal/evaluate",
        json={
            "person_id": "USER_001",
            "date": "2026-03-28",
            "transport": [{"mode": "car_petrol", "distance_km": 20}],
        },
    )
    assert resp.status_code == 422


def test_personal_missing_waste_treatment_rejected(client):
    resp = client.post(
        "/api/v1/carbon/personal/evaluate",
        json={
            "person_id": "USER_001",
            "date": "2026-03-28",
            "waste": [{"waste_type": "plastic", "quantity": 1, "unit": "kg"}],
        },
    )
    assert resp.status_code == 422


def test_carbon_factors_endpoint(client):
    resp = client.get("/api/v1/carbon/factors")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["provider"] == "climatiq"
    assert data["data_version"] == settings.CLIMATIQ_DATA_VERSION
    assert any(item["activity_type"] == "household_electricity" for item in data["factors"])
    assert any(
        item["activity_type"] == "household_electricity" and item["scope"] == "personal"
        for item in data["factors"]
    )
    assert any(
        item["activity_type"] == "waste_collection_truck" and item["scope"] == "fleet"
        for item in data["factors"]
    )


def test_personal_habits_catalog_endpoint(client):
    resp = client.get("/api/v1/carbon/personal/habits")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert any(item["habit_type"] == "shower" for item in data["habits"])
    assert any(item["habit_type"] == "washing_machine" for item in data["habits"])


def test_truck_carbon_latest_unknown_returns_404(client):
    resp = client.get("/api/v1/carbon/trucks/UNKNOWN/latest")
    assert resp.status_code == 404


def test_truck_carbon_latest_needs_clarification_with_single_state(client):
    payload = {
        "truck_id": "TRUCK_001",
        "waste_type": "organic",
        "current_position": {
            "latitude": 45.4642,
            "longitude": 9.1900,
            "timestamp": "2026-03-28T10:15:00Z",
        },
    }
    client.post("/api/v1/trucks/update", json=payload)

    resp = client.get("/api/v1/carbon/trucks/TRUCK_001/latest")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["scope"] == "fleet"
    assert data["status"] == "needs_clarification"
    assert data["evaluation"]["scope"] == "fleet"
    assert data["evaluation"]["status"] == "needs_clarification"
    assert data["segment_count"] == 0


def test_truck_carbon_latest_cumulative_success(client, monkeypatch):
    monkeypatch.setattr(settings, "CLIMATIQ_API_KEY", "test-key")
    monkeypatch.setattr("app.carbon.climatiq_client.ClimatiqClient.estimate", fake_estimate)

    first = {
        "truck_id": "TRUCK_001",
        "waste_type": "organic",
        "current_position": {
            "latitude": 45.0,
            "longitude": 9.0,
            "timestamp": "2026-03-28T10:15:00Z",
        },
    }
    second = {
        "truck_id": "TRUCK_001",
        "waste_type": "organic",
        "current_position": {
            "latitude": 45.1,
            "longitude": 9.0,
            "timestamp": "2026-03-28T10:20:00Z",
        },
    }
    client.post("/api/v1/trucks/update", json=first)
    client.post("/api/v1/trucks/update", json=second)

    resp = client.get("/api/v1/carbon/trucks/TRUCK_001/latest")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["scope"] == "fleet"
    assert data["status"] == "ok"
    assert data["segment_count"] == 1
    assert data["total_distance_km"] > 0
    assert data["evaluation"]["scope"] == "fleet"
    assert isclose(
        data["evaluation"]["co2e_kg"],
        round(data["total_distance_km"] * 0.5, 6),
        rel_tol=0,
        abs_tol=1e-6,
    )


def test_truck_carbon_history_pagination(client, monkeypatch):
    monkeypatch.setattr(settings, "CLIMATIQ_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.carbon.climatiq_client.ClimatiqClient.estimate_batch", fake_estimate_batch
    )

    updates = [
        {
            "truck_id": "TRUCK_001",
            "waste_type": "organic",
            "current_position": {
                "latitude": 45.0 + idx * 0.01,
                "longitude": 9.0,
                "timestamp": f"2026-03-28T10:{15 + idx:02d}:00Z",
            },
        }
        for idx in range(3)
    ]
    for payload in updates:
        client.post("/api/v1/trucks/update", json=payload)

    resp = client.get("/api/v1/carbon/trucks/TRUCK_001/history?page=1&page_size=1")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["scope"] == "fleet"
    assert data["total"] == 2
    assert len(data["records"]) == 1
    assert data["records"][0]["scope"] == "fleet"
    assert data["records"][0]["evaluation"]["scope"] == "fleet"
    assert data["records"][0]["to_version"] == 3


def test_carbon_evaluate_returns_503_when_provider_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "CLIMATIQ_API_KEY", None)
    resp = client.post(
        "/api/v1/carbon/evaluate",
        json={
            "activity_type": "household_electricity",
            "quantity": 5,
            "unit": "kWh",
        },
    )
    assert resp.status_code == 503

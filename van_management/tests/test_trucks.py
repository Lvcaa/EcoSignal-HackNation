PAYLOAD = {
    "truck_id": "TRUCK_001",
    "waste_type": "organic",
    "current_position": {
        "latitude": 45.4642,
        "longitude": 9.1900,
        "timestamp": "2026-03-28T10:15:00Z",
    },
}


def test_create_first_version(client):
    resp = client.post("/api/v1/trucks/update", json=PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["version"] == 1
    assert body["data"]["truck_id"] == "TRUCK_001"
    assert body["data"]["waste_type"] == "organic"


def test_second_version_increments(client):
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    resp = client.post("/api/v1/trucks/update", json=PAYLOAD)
    assert resp.status_code == 201
    assert resp.json()["data"]["version"] == 2


def test_history_returns_all_versions(client):
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    client.post("/api/v1/trucks/update", json=PAYLOAD)

    resp = client.get("/api/v1/trucks/TRUCK_001/history")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total"] == 3
    assert len(data["records"]) == 3
    # Most recent version first
    versions = [r["version"] for r in data["records"]]
    assert versions == [3, 2, 1]


def test_history_unknown_truck_returns_404(client):
    resp = client.get("/api/v1/trucks/UNKNOWN/history")
    assert resp.status_code == 404


def test_invalid_waste_type_rejected(client):
    bad = {**PAYLOAD, "waste_type": "nuclear"}
    resp = client.post("/api/v1/trucks/update", json=bad)
    assert resp.status_code == 422


def test_invalid_latitude_rejected(client):
    bad = {
        **PAYLOAD,
        "current_position": {
            "latitude": 999,
            "longitude": 9.19,
            "timestamp": "2026-03-28T10:15:00Z",
        },
    }
    resp = client.post("/api/v1/trucks/update", json=bad)
    assert resp.status_code == 422

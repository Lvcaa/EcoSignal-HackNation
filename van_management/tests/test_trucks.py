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


def test_latest_returns_most_recent_version(client):
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    client.post("/api/v1/trucks/update", json=PAYLOAD)

    resp = client.get("/api/v1/trucks/TRUCK_001/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["truck_id"] == "TRUCK_001"
    assert body["data"]["version"] == 2


def test_latest_unknown_truck_returns_404(client):
    resp = client.get("/api/v1/trucks/UNKNOWN/latest")
    assert resp.status_code == 404


def test_history_unknown_truck_returns_404(client):
    resp = client.get("/api/v1/trucks/UNKNOWN/history")
    assert resp.status_code == 404


def test_fleet_latest_empty(client):
    resp = client.get("/api/v1/trucks")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_fleet_latest_returns_one_row_per_truck(client):
    truck_002 = {**PAYLOAD, "truck_id": "TRUCK_002", "waste_type": "plastic"}

    # TRUCK_001 gets 3 updates, TRUCK_002 gets 2
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    client.post("/api/v1/trucks/update", json=truck_002)
    client.post("/api/v1/trucks/update", json=truck_002)

    resp = client.get("/api/v1/trucks")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert len(data) == 2
    by_id = {t["truck_id"]: t for t in data}
    assert by_id["TRUCK_001"]["version"] == 3
    assert by_id["TRUCK_002"]["version"] == 2


def test_fleet_latest_message_format(client):
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    resp = client.get("/api/v1/trucks")
    assert resp.json()["message"] == "Found 1 truck(s)"


def test_truck_ids_empty(client):
    resp = client.get("/api/v1/trucks/ids")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_truck_ids_returns_known_ids(client):
    truck_002 = {**PAYLOAD, "truck_id": "TRUCK_002"}
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    client.post("/api/v1/trucks/update", json=PAYLOAD)  # second version same truck
    client.post("/api/v1/trucks/update", json=truck_002)

    resp = client.get("/api/v1/trucks/ids")
    assert resp.status_code == 200
    ids = resp.json()["data"]
    assert sorted(ids) == ["TRUCK_001", "TRUCK_002"]


BATCH_PAYLOAD = {
    "company_id": "COMPANY_A",
    "updates": [
        {
            "truck_id": "TRUCK_001",
            "waste_type": "organic",
            "current_position": {"latitude": 45.46, "longitude": 9.19, "timestamp": "2026-03-28T10:15:00Z"},
        },
        {
            "truck_id": "TRUCK_002",
            "waste_type": "plastic",
            "current_position": {"latitude": 45.47, "longitude": 9.20, "timestamp": "2026-03-28T10:15:00Z"},
        },
    ],
}


def test_batch_creates_records(client):
    resp = client.post("/api/v1/trucks/batch", json=BATCH_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["company_id"] == "COMPANY_A"
    assert body["data"]["accepted"] == 2
    assert len(body["data"]["records"]) == 2


def test_batch_first_versions_start_at_one(client):
    resp = client.post("/api/v1/trucks/batch", json=BATCH_PAYLOAD)
    records = {r["truck_id"]: r for r in resp.json()["data"]["records"]}
    assert records["TRUCK_001"]["version"] == 1
    assert records["TRUCK_002"]["version"] == 1


def test_batch_increments_existing_version(client):
    # seed TRUCK_001 to v2 via single-update endpoint
    client.post("/api/v1/trucks/update", json=PAYLOAD)
    client.post("/api/v1/trucks/update", json=PAYLOAD)

    resp = client.post("/api/v1/trucks/batch", json=BATCH_PAYLOAD)
    records = {r["truck_id"]: r for r in resp.json()["data"]["records"]}
    assert records["TRUCK_001"]["version"] == 3   # continued from v2
    assert records["TRUCK_002"]["version"] == 1   # new truck


def test_batch_intra_batch_duplicate_stacks_versions(client):
    batch = {
        "company_id": "COMPANY_A",
        "updates": [
            {"truck_id": "TRUCK_001", "waste_type": "organic",
             "current_position": {"latitude": 45.46, "longitude": 9.19, "timestamp": "2026-03-28T10:15:00Z"}},
            {"truck_id": "TRUCK_001", "waste_type": "organic",
             "current_position": {"latitude": 45.47, "longitude": 9.20, "timestamp": "2026-03-28T10:16:00Z"}},
        ],
    }
    resp = client.post("/api/v1/trucks/batch", json=batch)
    assert resp.status_code == 201
    versions = [r["version"] for r in resp.json()["data"]["records"]]
    assert versions == [1, 2]


def test_batch_company_id_stored_on_records(client):
    resp = client.post("/api/v1/trucks/batch", json=BATCH_PAYLOAD)
    for rec in resp.json()["data"]["records"]:
        assert rec["company_id"] == "COMPANY_A"


def test_batch_empty_updates_rejected(client):
    resp = client.post("/api/v1/trucks/batch", json={"company_id": "COMPANY_A", "updates": []})
    assert resp.status_code == 422


def test_batch_missing_company_id_rejected(client):
    resp = client.post("/api/v1/trucks/batch", json={"updates": BATCH_PAYLOAD["updates"]})
    assert resp.status_code == 422


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

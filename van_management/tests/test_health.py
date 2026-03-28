def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "OK"


def test_version(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["name"] == "EcoSignal Backend"
    assert "version" in body["data"]

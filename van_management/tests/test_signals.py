import io


SIGNAL_PAYLOAD = {
    "title": "Incendio boschivo",
    "description": "Fumo visibile dalla strada provinciale SP45, lato nord",
    "signal_type": "emergenza",
    "latitude": 45.4642,
    "longitude": 9.1900,
}


# --- Signal CRUD ---


def test_create_signal(client):
    resp = client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Incendio boschivo"
    assert body["data"]["signal_type"] == "emergenza"
    assert body["data"]["latitude"] == 45.4642
    assert body["data"]["attachments"] == []


def test_create_signal_info_type(client):
    payload = {**SIGNAL_PAYLOAD, "signal_type": "info"}
    resp = client.post("/api/v1/signals", json=payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["signal_type"] == "info"


def test_create_signal_invalid_type_rejected(client):
    payload = {**SIGNAL_PAYLOAD, "signal_type": "warning"}
    resp = client.post("/api/v1/signals", json=payload)
    assert resp.status_code == 422


def test_create_signal_invalid_latitude_rejected(client):
    payload = {**SIGNAL_PAYLOAD, "latitude": 999}
    resp = client.post("/api/v1/signals", json=payload)
    assert resp.status_code == 422


def test_create_signal_invalid_longitude_rejected(client):
    payload = {**SIGNAL_PAYLOAD, "longitude": -200}
    resp = client.post("/api/v1/signals", json=payload)
    assert resp.status_code == 422


def test_create_signal_empty_title_rejected(client):
    payload = {**SIGNAL_PAYLOAD, "title": ""}
    resp = client.post("/api/v1/signals", json=payload)
    assert resp.status_code == 422


def test_get_signal(client):
    create_resp = client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    signal_id = create_resp.json()["data"]["id"]

    resp = client.get(f"/api/v1/signals/{signal_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == signal_id


def test_get_signal_not_found(client):
    resp = client.get("/api/v1/signals/99999")
    assert resp.status_code == 404


def test_list_signals_empty(client):
    resp = client.get("/api/v1/signals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["total"] == 0
    assert body["data"]["signals"] == []


def test_list_signals_returns_all(client):
    client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    client.post("/api/v1/signals", json={**SIGNAL_PAYLOAD, "title": "Altro segnale"})

    resp = client.get("/api/v1/signals")
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 2
    assert len(resp.json()["data"]["signals"]) == 2


def test_list_signals_pagination(client):
    for i in range(5):
        client.post("/api/v1/signals", json={**SIGNAL_PAYLOAD, "title": f"Signal {i}"})

    resp = client.get("/api/v1/signals?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 5
    assert len(data["signals"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_delete_signal(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.signal_service.settings.UPLOAD_DIR", str(tmp_path))

    create_resp = client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    signal_id = create_resp.json()["data"]["id"]

    resp = client.delete(f"/api/v1/signals/{signal_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = client.get(f"/api/v1/signals/{signal_id}")
    assert resp.status_code == 404


def test_delete_signal_not_found(client):
    resp = client.delete("/api/v1/signals/99999")
    assert resp.status_code == 404


# --- Attachments ---


def test_upload_attachment(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.signal_service.settings.UPLOAD_DIR", str(tmp_path))

    create_resp = client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    signal_id = create_resp.json()["data"]["id"]

    file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    resp = client.post(
        f"/api/v1/signals/{signal_id}/attachments",
        files=[("files", ("test.png", io.BytesIO(file_content), "image/png"))],
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["original_filename"] == "test.png"
    assert body["data"][0]["content_type"] == "image/png"


def test_upload_multiple_files(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.signal_service.settings.UPLOAD_DIR", str(tmp_path))

    create_resp = client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    signal_id = create_resp.json()["data"]["id"]

    files = [
        ("files", ("a.png", io.BytesIO(b"\x89PNG" + b"\x00" * 50), "image/png")),
        ("files", ("b.jpg", io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 50), "image/jpeg")),
    ]
    resp = client.post(f"/api/v1/signals/{signal_id}/attachments", files=files)
    assert resp.status_code == 201
    assert len(resp.json()["data"]) == 2


def test_upload_attachment_signal_not_found(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.signal_service.settings.UPLOAD_DIR", str(tmp_path))

    file_content = b"\x89PNG" + b"\x00" * 100
    resp = client.post(
        "/api/v1/signals/99999/attachments",
        files=[("files", ("test.png", io.BytesIO(file_content), "image/png"))],
    )
    assert resp.status_code == 404


def test_upload_attachment_invalid_content_type(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.signal_service.settings.UPLOAD_DIR", str(tmp_path))

    create_resp = client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    signal_id = create_resp.json()["data"]["id"]

    resp = client.post(
        f"/api/v1/signals/{signal_id}/attachments",
        files=[("files", ("test.txt", io.BytesIO(b"hello"), "text/plain"))],
    )
    assert resp.status_code == 400


def test_download_attachment(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.signal_service.settings.UPLOAD_DIR", str(tmp_path))

    create_resp = client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    signal_id = create_resp.json()["data"]["id"]

    file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    upload_resp = client.post(
        f"/api/v1/signals/{signal_id}/attachments",
        files=[("files", ("test.png", io.BytesIO(file_content), "image/png"))],
    )
    attachment_id = upload_resp.json()["data"][0]["id"]

    resp = client.get(f"/api/v1/signals/{signal_id}/attachments/{attachment_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content == file_content


def test_download_attachment_not_found(client):
    resp = client.get("/api/v1/signals/1/attachments/99999")
    assert resp.status_code == 404


def test_signal_with_attachments_shown_in_get(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.signal_service.settings.UPLOAD_DIR", str(tmp_path))

    create_resp = client.post("/api/v1/signals", json=SIGNAL_PAYLOAD)
    signal_id = create_resp.json()["data"]["id"]

    file_content = b"\x89PNG" + b"\x00" * 100
    client.post(
        f"/api/v1/signals/{signal_id}/attachments",
        files=[("files", ("a.png", io.BytesIO(file_content), "image/png"))],
    )

    resp = client.get(f"/api/v1/signals/{signal_id}")
    assert resp.status_code == 200
    assert len(resp.json()["data"]["attachments"]) == 1

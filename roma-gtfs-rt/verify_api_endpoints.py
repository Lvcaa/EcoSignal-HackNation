#!/usr/bin/env python3
"""
Verifica di **ampiezza** (ogni endpoint documentato), non di volume dati.

Riferimento: `Van Management API Reference.md`
  - Endpoint Summary (trucks)
  - Signals Endpoint Summary (signals)

Uso:
  python3 verify_api_endpoints.py
  python3 verify_api_endpoints.py --skip-write
  python3 verify_api_endpoints.py --trucks-only
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
import uuid
from urllib.parse import quote

import requests

DEFAULT_BASE = "https://dayana-nonfulminating-novella.ngrok-free.dev"

PROBE_UNKNOWN_TRUCK = "UNKNOWN_TRUCK_ENDPOINT_PROBE"

SKIP = {"ngrok-skip-browser-warning": "true"}
JSON_POST = {**SKIP, "Content-Type": "application/json"}

# Van Management API Reference.md — Endpoint Summary (trucks)
TRUCK_ENDPOINTS: list[tuple[str, str, str]] = [
    ("GET", "/health", "Liveness check"),
    ("GET", "/version", "Service metadata"),
    ("GET", "/api/v1/trucks", "Fleet-wide latest state snapshot"),
    ("GET", "/api/v1/trucks/ids", "List all known truck IDs"),
    ("GET", "/api/v1/trucks/{truck_id}/latest", "Fetch the current state for one truck"),
    ("GET", "/api/v1/trucks/{truck_id}/history", "Fetch version history for one truck"),
    ("POST", "/api/v1/trucks/update", "Create a new truck state version"),
    ("POST", "/api/v1/trucks/batch", "Create many truck state versions in one request"),
]

# Signals Endpoint Summary
SIGNAL_ENDPOINTS: list[tuple[str, str, str]] = [
    ("POST", "/api/v1/signals", "Create a new signal"),
    ("GET", "/api/v1/signals", "List all signals (paginated)"),
    ("GET", "/api/v1/signals/{signal_id}", "Get a single signal with attachments"),
    ("POST", "/api/v1/signals/{signal_id}/attachments", "Upload image attachments"),
    ("GET", "/api/v1/signals/{signal_id}/attachments/{attachment_id}", "Download an image"),
    ("DELETE", "/api/v1/signals/{signal_id}", "Delete a signal and its attachments"),
]

# PNG 1x1 valido (minimo) per multipart
MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}", file=sys.stderr)


def get_json(url: str, timeout: float) -> tuple[int, dict | list | None]:
    r = requests.get(url, headers=SKIP, timeout=timeout)
    try:
        body = r.json() if r.text else None
    except json.JSONDecodeError:
        body = None
    return r.status_code, body


def check_envelope(body: dict | None, path: str) -> bool:
    if not isinstance(body, dict):
        fail(f"{path}: risposta non è JSON oggetto")
        return False
    if "success" not in body:
        fail(f"{path}: manca envelope success")
        return False
    return True


def verify_trucks(
    base: str,
    t: float,
    skip_write: bool,
    checked: dict[str, bool | str],
) -> None:
    r = requests.get(f"{base}/health", headers=SKIP, timeout=t)
    if r.status_code == 200 and check_envelope(r.json(), "/health"):
        ok("GET /health → 200 + envelope")
        checked["GET /health"] = True
    else:
        fail(f"GET /health → {r.status_code}")
        checked["GET /health"] = False

    r = requests.get(f"{base}/version", headers=SKIP, timeout=t)
    if r.status_code == 200 and check_envelope(r.json(), "/version"):
        ok("GET /version → 200 + envelope")
        checked["GET /version"] = True
    else:
        fail(f"GET /version → {r.status_code}")
        checked["GET /version"] = False

    sample_id: str | None = None
    code, data = get_json(f"{base}/api/v1/trucks", t)
    if code == 200 and isinstance(data, dict) and data.get("success") is True:
        ok("GET /api/v1/trucks → 200 + envelope")
        checked["GET /api/v1/trucks"] = True
        rows = data.get("data")
        if isinstance(rows, list) and rows:
            first = rows[0]
            if isinstance(first, dict) and first.get("truck_id"):
                sample_id = str(first["truck_id"])
    else:
        fail(f"GET /api/v1/trucks → {code}")
        checked["GET /api/v1/trucks"] = False

    code, data = get_json(f"{base}/api/v1/trucks/ids", t)
    if code == 200 and isinstance(data, dict) and data.get("success") is True:
        ok("GET /api/v1/trucks/ids → 200 + envelope")
        checked["GET /api/v1/trucks/ids"] = True
        if not sample_id and isinstance(data.get("data"), list) and data["data"]:
            sample_id = str(data["data"][0])
    else:
        fail(f"GET /api/v1/trucks/ids → {code}")
        checked["GET /api/v1/trucks/ids"] = False

    tid = sample_id or PROBE_UNKNOWN_TRUCK
    code, data = get_json(f"{base}/api/v1/trucks/{quote(tid, safe='')}/latest", t)
    if code == 200 and isinstance(data, dict) and data.get("success") is True:
        ok(f"GET /api/v1/trucks/{{truck_id}}/latest → 200")
        checked["GET /api/v1/trucks/{truck_id}/latest"] = True
    elif code == 404:
        ok("GET /api/v1/trucks/{truck_id}/latest → 404 (route verificata)")
        checked["GET /api/v1/trucks/{truck_id}/latest"] = True
    else:
        fail(f"GET .../latest → {code}")
        checked["GET /api/v1/trucks/{truck_id}/latest"] = False

    code, data = get_json(
        f"{base}/api/v1/trucks/{quote(tid, safe='')}/history?page=1&page_size=5", t
    )
    if code == 200 and isinstance(data, dict) and data.get("success") is True:
        ok("GET /api/v1/trucks/{truck_id}/history → 200")
        checked["GET /api/v1/trucks/{truck_id}/history"] = True
    elif code == 404:
        ok("GET /api/v1/trucks/{truck_id}/history → 404 (route verificata)")
        checked["GET /api/v1/trucks/{truck_id}/history"] = True
    else:
        fail(f"GET .../history → {code}")
        checked["GET /api/v1/trucks/{truck_id}/history"] = False

    if skip_write:
        checked["POST /api/v1/trucks/update"] = "skip"
        checked["POST /api/v1/trucks/batch"] = "skip"
        return

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    uid = uuid.uuid4().hex[:8]
    truck_probe = f"VERIFY_{uid}"
    body = {
        "truck_id": truck_probe,
        "waste_type": "mixed",
        "current_position": {
            "latitude": 41.9028,
            "longitude": 12.4964,
            "timestamp": ts,
        },
    }
    r = requests.post(
        f"{base}/api/v1/trucks/update",
        data=json.dumps(body).encode("utf-8"),
        headers=JSON_POST,
        timeout=t,
    )
    if r.status_code in (200, 201):
        ok("POST /api/v1/trucks/update → 201/200")
        checked["POST /api/v1/trucks/update"] = True
    else:
        fail(f"POST /api/v1/trucks/update → {r.status_code} {r.text[:200]}")
        checked["POST /api/v1/trucks/update"] = False

    batch_body = {
        "company_id": f"VERIFY_CO_{uid}",
        "updates": [
            {
                "truck_id": f"VERIFY_BATCH_{uid}",
                "waste_type": "mixed",
                "current_position": {
                    "latitude": 41.903,
                    "longitude": 12.497,
                    "timestamp": ts,
                },
            }
        ],
    }
    r = requests.post(
        f"{base}/api/v1/trucks/batch",
        data=json.dumps(batch_body).encode("utf-8"),
        headers=JSON_POST,
        timeout=t,
    )
    if r.status_code in (200, 201):
        ok("POST /api/v1/trucks/batch → 201/200")
        checked["POST /api/v1/trucks/batch"] = True
    else:
        fail(f"POST /api/v1/trucks/batch → {r.status_code} {r.text[:200]}")
        checked["POST /api/v1/trucks/batch"] = False


def verify_signals(
    base: str,
    t: float,
    skip_write: bool,
    checked: dict[str, bool | str],
) -> None:
    if skip_write:
        # Solo GET: lista + 404 su id inesistente
        code, data = get_json(f"{base}/api/v1/signals?page=1&page_size=5", t)
        if code == 200 and isinstance(data, dict) and data.get("success") is True:
            ok("GET /api/v1/signals → 200 + envelope")
            checked["GET /api/v1/signals"] = True
        else:
            fail(f"GET /api/v1/signals → {code}")
            checked["GET /api/v1/signals"] = False

        code, _data = get_json(f"{base}/api/v1/signals/999999999", t)
        if code == 404:
            ok("GET /api/v1/signals/{signal_id} → 404 (route verificata)")
            checked["GET /api/v1/signals/{signal_id}"] = True
        elif code == 200:
            ok("GET /api/v1/signals/{signal_id} → 200")
            checked["GET /api/v1/signals/{signal_id}"] = True
        else:
            fail(f"GET /api/v1/signals/{{id}} → {code}")
            checked["GET /api/v1/signals/{signal_id}"] = False

        for k in (
            "POST /api/v1/signals",
            "POST /api/v1/signals/{signal_id}/attachments",
            "GET /api/v1/signals/{signal_id}/attachments/{attachment_id}",
            "DELETE /api/v1/signals/{signal_id}",
        ):
            checked[k] = "skip"
        return

    uid = uuid.uuid4().hex[:6]
    create_body = {
        "title": f"verify probe {uid}",
        "description": "endpoint breadth test",
        "signal_type": "info",
        "latitude": 41.9028,
        "longitude": 12.4964,
    }
    r = requests.post(
        f"{base}/api/v1/signals",
        data=json.dumps(create_body).encode("utf-8"),
        headers=JSON_POST,
        timeout=t,
    )
    if r.status_code not in (200, 201):
        fail(f"POST /api/v1/signals → {r.status_code} {r.text[:300]}")
        for k in (
            "POST /api/v1/signals",
            "GET /api/v1/signals",
            "GET /api/v1/signals/{signal_id}",
            "POST /api/v1/signals/{signal_id}/attachments",
            "GET /api/v1/signals/{signal_id}/attachments/{attachment_id}",
            "DELETE /api/v1/signals/{signal_id}",
        ):
            checked[k] = False
        return

    checked["POST /api/v1/signals"] = True
    ok("POST /api/v1/signals → 201/200")
    try:
        sig_id = r.json()["data"]["id"]
    except (KeyError, TypeError, ValueError):
        fail("POST /signals: impossibile leggere data.id")
        for k in (
            "GET /api/v1/signals",
            "GET /api/v1/signals/{signal_id}",
            "POST /api/v1/signals/{signal_id}/attachments",
            "GET /api/v1/signals/{signal_id}/attachments/{attachment_id}",
            "DELETE /api/v1/signals/{signal_id}",
        ):
            checked[k] = False
        return

    code, data = get_json(f"{base}/api/v1/signals?page=1&page_size=10", t)
    if code == 200 and isinstance(data, dict) and data.get("success") is True:
        ok("GET /api/v1/signals → 200 + envelope")
        checked["GET /api/v1/signals"] = True
    else:
        fail(f"GET /api/v1/signals → {code}")
        checked["GET /api/v1/signals"] = False

    code, data = get_json(f"{base}/api/v1/signals/{sig_id}", t)
    if code == 200 and isinstance(data, dict) and data.get("success") is True:
        ok(f"GET /api/v1/signals/{{signal_id}} → 200 (id={sig_id})")
        checked["GET /api/v1/signals/{signal_id}"] = True
    else:
        fail(f"GET /api/v1/signals/{{id}} → {code}")
        checked["GET /api/v1/signals/{signal_id}"] = False

    files = [("files", (f"probe_{uid}.png", io.BytesIO(MINIMAL_PNG), "image/png"))]
    r = requests.post(
        f"{base}/api/v1/signals/{sig_id}/attachments",
        headers=SKIP,
        files=files,
        timeout=t,
    )
    att_id: int | None = None
    if r.status_code in (200, 201):
        checked["POST /api/v1/signals/{signal_id}/attachments"] = True
        ok("POST /api/v1/signals/{signal_id}/attachments → 201/200 (multipart, 1 PNG)")
        try:
            resp = r.json()
            arr = resp.get("data")
            if isinstance(arr, list) and arr:
                att_id = arr[0].get("id")
        except (json.JSONDecodeError, TypeError):
            pass
    else:
        fail(f"POST .../attachments → {r.status_code} {r.text[:300]}")
        checked["POST /api/v1/signals/{signal_id}/attachments"] = False

    if att_id is not None:
        rd = requests.get(
            f"{base}/api/v1/signals/{sig_id}/attachments/{att_id}",
            headers=SKIP,
            timeout=t,
        )
        if rd.status_code == 200 and len(rd.content) > 0:
            ok("GET .../attachments/{attachment_id} → 200 (binary)")
            checked["GET /api/v1/signals/{signal_id}/attachments/{attachment_id}"] = True
        else:
            fail(f"GET attachment download → {rd.status_code}")
            checked["GET /api/v1/signals/{signal_id}/attachments/{attachment_id}"] = False
    else:
        code, _ = get_json(
            f"{base}/api/v1/signals/{sig_id}/attachments/999999", t
        )
        if code == 404:
            ok("GET .../attachments/{attachment_id} → 404 (route verificata)")
            checked["GET /api/v1/signals/{signal_id}/attachments/{attachment_id}"] = True
        else:
            checked["GET /api/v1/signals/{signal_id}/attachments/{attachment_id}"] = False

    rd = requests.delete(f"{base}/api/v1/signals/{sig_id}", headers=SKIP, timeout=t)
    if rd.status_code == 200:
        try:
            body = rd.json() if rd.text else {}
            if isinstance(body, dict) and body.get("success") is True:
                ok(f"DELETE /api/v1/signals/{{signal_id}} → 200 (id={sig_id})")
            else:
                ok("DELETE /api/v1/signals/{signal_id} → 200")
        except json.JSONDecodeError:
            ok("DELETE /api/v1/signals/{signal_id} → 200")
        checked["DELETE /api/v1/signals/{signal_id}"] = True
    elif rd.status_code == 204:
        ok(f"DELETE /api/v1/signals/{{signal_id}} → 204")
        checked["DELETE /api/v1/signals/{signal_id}"] = True
    else:
        fail(f"DELETE /api/v1/signals/{{id}} → {rd.status_code} {rd.text[:200]}")
        checked["DELETE /api/v1/signals/{signal_id}"] = False


def _print_matrix(
    checked: dict[str, bool | str],
    all_endpoints: list[tuple[str, str, str]],
    write_skipped: bool,
) -> None:
    print("\n--- Copertura vs Van Management API Reference.md ---")
    for method, path, purpose in all_endpoints:
        key = f"{method} {path}"
        v = checked.get(key)
        if v is True:
            status = "sì"
        elif v == "skip":
            status = "saltato"
        else:
            status = "no"
        print(f"  {method:6} {path:50}  {purpose[:36]:36}  [{status}]")

    if write_skipped:
        print("\nModalità --skip-write: POST trucks e operazioni signals in scrittura saltate.")
        return

    all_ok = all(checked.get(f"{m} {p}") is True for m, p, _ in all_endpoints)
    if all_ok:
        print(f"\nTutti i {len(all_endpoints)} endpoint risultano verificati in questa run.")
    else:
        print("\nAlcuni endpoint non risultano OK; vedi [FAIL] sopra.", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description="Verifica ampiezza API trucks + signals")
    ap.add_argument(
        "--base-url",
        default=os.environ.get("VAN_BASE_URL", DEFAULT_BASE).rstrip("/"),
    )
    ap.add_argument("--skip-write", action="store_true")
    ap.add_argument("--trucks-only", action="store_true", help="Solo endpoint trucks")
    ap.add_argument("--timeout", type=float, default=45.0)
    args = ap.parse_args()

    base = args.base_url
    t = args.timeout
    checked: dict[str, bool | str] = {}

    print(f"Base URL: {base}")
    if args.trucks_only:
        print("Riferimento: Van Management API Reference.md — Endpoint Summary (trucks)\n")
    else:
        print(
            "Riferimento: Van Management API Reference.md — trucks + Signals Endpoint Summary\n"
        )

    verify_trucks(base, t, args.skip_write, checked)

    if args.trucks_only:
        _print_matrix(checked, TRUCK_ENDPOINTS, args.skip_write)
        return

    print("\n--- Signals ---\n")
    verify_signals(base, t, args.skip_write, checked)

    all_ep = TRUCK_ENDPOINTS + SIGNAL_ENDPOINTS
    _print_matrix(checked, all_ep, args.skip_write)


if __name__ == "__main__":
    main()

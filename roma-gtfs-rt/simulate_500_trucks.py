#!/usr/bin/env python3
"""
Simula 500 truck (TRUCK_1 … TRUCK_500) che si muovono nell'area di Roma.
Ogni secondo invia un batch di posizioni aggiornate a /api/v1/trucks/batch.
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from datetime import datetime, timezone

import requests

BASE_URL = "http://localhost:8000"
BATCH_URL = f"{BASE_URL}/api/v1/trucks/batch"
COMPANY_ID = "ROMA_SIM"
NUM_TRUCKS = 500

ROME_CENTER_LAT = 41.9028
ROME_CENTER_LON = 12.4964
SPREAD = 0.25  # ~25 km radius — copre tutta l'area metropolitana

WASTE_TYPES = ["organic", "paper", "plastic", "glass", "mixed"]

HEADERS = {"Content-Type": "application/json"}


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_trucks() -> list[dict]:
    trucks = []
    for i in range(1, NUM_TRUCKS + 1):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0, SPREAD)
        lat = ROME_CENTER_LAT + radius * math.sin(angle)
        lon = ROME_CENTER_LON + radius * math.cos(angle)
        trucks.append({
            "id": i,
            "truck_id": f"TRUCK_{i}",
            "waste_type": WASTE_TYPES[i % len(WASTE_TYPES)],
            "lat": lat,
            "lon": lon,
            "heading": random.uniform(0, 2 * math.pi),
            "speed": random.uniform(0.00005, 0.0003),
        })
    return trucks


def move_trucks(trucks: list[dict]) -> None:
    for t in trucks:
        t["heading"] += random.uniform(-0.3, 0.3)
        t["lat"] += t["speed"] * math.sin(t["heading"])
        t["lon"] += t["speed"] * math.cos(t["heading"])
        t["speed"] = max(0.00002, min(0.0004, t["speed"] + random.uniform(-0.00003, 0.00003)))


def send_batch(trucks: list[dict]) -> None:
    ts = iso_now()
    updates = [
        {
            "truck_id": t["truck_id"],
            "waste_type": t["waste_type"],
            "current_position": {
                "latitude": round(t["lat"], 6),
                "longitude": round(t["lon"], 6),
                "timestamp": ts,
            },
        }
        for t in trucks
    ]

    for i in range(0, len(updates), 500):
        chunk = updates[i : i + 500]
        payload = {"company_id": COMPANY_ID, "updates": chunk}
        try:
            r = requests.post(
                BATCH_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=HEADERS,
                timeout=10,
            )
            if r.status_code in (200, 201):
                body = r.json()
                accepted = body.get("data", {}).get("accepted", "?")
                print(f"[{ts}] batch {i // 500 + 1}: {accepted} accepted", flush=True)
            else:
                print(f"[{ts}] batch {i // 500 + 1}: HTTP {r.status_code}", file=sys.stderr, flush=True)
        except requests.RequestException as e:
            print(f"[{ts}] errore: {e}", file=sys.stderr, flush=True)


def main() -> None:
    print(f"Inizializzazione {NUM_TRUCKS} truck nell'area di Roma...", flush=True)
    trucks = init_trucks()

    print("Invio primo batch (creazione)...", flush=True)
    send_batch(trucks)

    print("Loop: aggiornamento posizioni ogni secondo. Ctrl+C per fermare.", flush=True)
    while True:
        time.sleep(1)
        move_trucks(trucks)
        send_batch(trucks)


if __name__ == "__main__":
    main()

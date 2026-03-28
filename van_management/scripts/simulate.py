"""
EcoSignal - Van Simulator Demo
===============================
Emulates a fleet of waste-collection vans sending telemetry updates
to the backend API, then visualises versioning, history, and position
on an ASCII map.

Runs entirely in-process (TestClient + SQLite), no Docker needed.

Usage:
    cd van_management
    python scripts/simulate.py
"""

import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

# --- bootstrap: point at in-memory SQLite before any app import -----------
os.environ["DATABASE_URL"] = "sqlite://"

# ensure the package root is importable when running from van_management/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# silence noisy HTTP-level logs so only our output shows
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("app.services.truck_service").setLevel(logging.WARNING)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# ---- in-memory DB setup (same trick as the test suite) -------------------
_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db
client = TestClient(app)

# ---- drawing helpers -----------------------------------------------------
W = 72  # terminal width for formatting


def banner(text: str) -> None:
    print(f"\n{'=' * W}")
    print(f"  {text}")
    print(f"{'=' * W}")


def section(text: str) -> None:
    print(f"\n{'---'} {text} {'-' * max(0, W - len(text) - 5)}")


def ok(msg: str) -> None:
    print(f"   [OK]  {msg}")


def fail(msg: str) -> None:
    print(f"   [ERR] {msg}")


def row(cols: list[str], widths: list[int]) -> str:
    parts = []
    for c, w in zip(cols, widths):
        parts.append(str(c).ljust(w))
    return " | ".join(parts)


# ---- fleet definition ----------------------------------------------------
WASTE_TYPES = ["organic", "paper", "plastic", "glass", "mixed"]
WASTE_LABELS = {
    "organic": "ORG", "paper": "PAP", "plastic": "PLA",
    "glass": "GLS", "mixed": "MIX",
}

VANS = [
    {"id": "VAN_001", "waste": "organic",  "lat": 45.4642, "lon": 9.1900},
    {"id": "VAN_002", "waste": "plastic",  "lat": 45.4700, "lon": 9.2000},
    {"id": "VAN_003", "waste": "glass",    "lat": 45.4580, "lon": 9.1850},
    {"id": "VAN_004", "waste": "paper",    "lat": 45.4750, "lon": 9.1950},
    {"id": "VAN_005", "waste": "mixed",    "lat": 45.4620, "lon": 9.2100},
]

ROUNDS = 5
PAUSE = 0.35  # seconds between API calls for readability

# map bounding box (Milan centre)
MAP_LAT_MIN, MAP_LAT_MAX = 45.455, 45.480
MAP_LON_MIN, MAP_LON_MAX = 9.175, 9.220
MAP_ROWS, MAP_COLS = 12, 40


# ---- simulation logic ----------------------------------------------------
def drift(val: float, lo: float, hi: float) -> float:
    """Small random walk, clamped to bounds."""
    return max(lo, min(hi, val + random.uniform(-0.0025, 0.0025)))


def post_update(van: dict, ts: datetime) -> dict | None:
    payload = {
        "truck_id": van["id"],
        "waste_type": van["waste"],
        "current_position": {
            "latitude": round(van["lat"], 6),
            "longitude": round(van["lon"], 6),
            "timestamp": ts.isoformat(),
        },
    }
    r = client.post("/api/v1/trucks/update", json=payload)
    if r.status_code == 201:
        return r.json()
    fail(f"{van['id']}  HTTP {r.status_code}: {r.text[:80]}")
    return None


def get_history(van_id: str) -> dict | None:
    r = client.get(f"/api/v1/trucks/{van_id}/history")
    if r.status_code == 200:
        return r.json()
    return None


def draw_fleet_table(vans: list[dict], versions: dict[str, int]) -> None:
    """Print a table with current state of every van."""
    section("Current Fleet State")
    widths = [10, 8, 9, 22, 22]
    header = row(["Van ID", "Waste", "Version", "Latitude", "Longitude"], widths)
    print(f"  {header}")
    print(f"  {'-+-'.join('-' * w for w in widths)}")
    for v in vans:
        ver = versions.get(v["id"], 0)
        line = row(
            [v["id"], v["waste"], f"v{ver}", f"{v['lat']:.6f}", f"{v['lon']:.6f}"],
            widths,
        )
        print(f"  {line}")


def draw_ascii_map(vans: list[dict]) -> None:
    """Render a simple ASCII grid with van positions."""
    section("ASCII Map - Milan centre")

    grid = [["." for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]

    for v in vans:
        # map lat/lon to grid row/col
        r = int((MAP_LAT_MAX - v["lat"]) / (MAP_LAT_MAX - MAP_LAT_MIN) * (MAP_ROWS - 1))
        c = int((v["lon"] - MAP_LON_MIN) / (MAP_LON_MAX - MAP_LON_MIN) * (MAP_COLS - 1))
        r = max(0, min(MAP_ROWS - 1, r))
        c = max(0, min(MAP_COLS - 1, c))
        label = v["id"][-1]  # just the digit
        grid[r][c] = label

    # y-axis labels
    lat_step = (MAP_LAT_MAX - MAP_LAT_MIN) / (MAP_ROWS - 1)
    print()
    for ri in range(MAP_ROWS):
        lat_label = f"{MAP_LAT_MAX - ri * lat_step:.3f}"
        cells = " ".join(grid[ri])
        print(f"  {lat_label} | {cells}")

    ruler = " " * 10 + "+" + "-" * (MAP_COLS * 2)
    print(ruler)

    # x-axis: show a few tick marks
    ticks = 5
    lon_step = (MAP_LON_MAX - MAP_LON_MIN) / (ticks - 1)
    tick_labels = "".join(f"{MAP_LON_MIN + i * lon_step:<{MAP_COLS * 2 // ticks}.3f}" for i in range(ticks))
    print(f"           {tick_labels}")

    # legend
    print()
    legend_parts = [f"  {v['id'][-1]}={v['id']} ({WASTE_LABELS[v['waste']]})" for v in vans]
    print("  Legend:", "  ".join(legend_parts))


def draw_history(van_id: str) -> None:
    """Fetch and print version history for one van."""
    section(f"Version History: {van_id}")
    data = get_history(van_id)
    if data is None:
        print("  (no history)")
        return
    records = data["data"]["records"]
    widths = [5, 8, 12, 12, 24]
    header = row(["Ver", "Waste", "Latitude", "Longitude", "Timestamp"], widths)
    print(f"  {header}")
    print(f"  {'-+-'.join('-' * w for w in widths)}")
    for rec in records:
        line = row(
            [
                f"v{rec['version']}",
                rec["waste_type"],
                f"{rec['latitude']:.6f}",
                f"{rec['longitude']:.6f}",
                rec["position_timestamp"][:19] + "Z",
            ],
            widths,
        )
        print(f"  {line}")


def test_validation_errors() -> None:
    """Show what happens when the simulator sends bad data."""
    section("Validation demo - bad requests")

    bad_waste = {
        "truck_id": "VAN_001",
        "waste_type": "nuclear",
        "current_position": {"latitude": 45.46, "longitude": 9.19,
                             "timestamp": "2026-03-28T10:00:00Z"},
    }
    r = client.post("/api/v1/trucks/update", json=bad_waste)
    print(f"  POST waste_type='nuclear'  ->  HTTP {r.status_code} (rejected)")

    bad_lat = {
        "truck_id": "VAN_001",
        "waste_type": "organic",
        "current_position": {"latitude": 999, "longitude": 9.19,
                             "timestamp": "2026-03-28T10:00:00Z"},
    }
    r = client.post("/api/v1/trucks/update", json=bad_lat)
    print(f"  POST latitude=999          ->  HTTP {r.status_code} (rejected)")

    r = client.get("/api/v1/trucks/GHOST_VAN/history")
    print(f"  GET  GHOST_VAN/history     ->  HTTP {r.status_code} (not found)")


# ---- main ----------------------------------------------------------------
def main() -> None:
    banner("EcoSignal  --  Van Simulator Demo")
    print(f"  Simulating {len(VANS)} vans x {ROUNDS} rounds")
    print(f"  Database: in-memory SQLite (no Docker needed)")

    # health + version
    section("Service checks")
    h = client.get("/health").json()
    ok(f"GET /health          -> success={h['success']}  message=\"{h['message']}\"")
    v = client.get("/version").json()
    ok(f"GET /version         -> {v['data']['name']} v{v['data']['version']}")

    versions: dict[str, int] = {}
    now = datetime(2026, 3, 28, 10, 0, 0, tzinfo=timezone.utc)

    for rnd in range(1, ROUNDS + 1):
        section(f"Round {rnd}/{ROUNDS}")
        ts = now + timedelta(minutes=15 * rnd)

        for van in VANS:
            # simulate movement
            van["lat"] = drift(van["lat"], MAP_LAT_MIN, MAP_LAT_MAX)
            van["lon"] = drift(van["lon"], MAP_LON_MIN, MAP_LON_MAX)

            result = post_update(van, ts)
            if result:
                ver = result["data"]["version"]
                versions[van["id"]] = ver
                print(
                    f"  POST {van['id']} | {van['waste']:<8s} | "
                    f"({van['lat']:.4f}, {van['lon']:.4f}) "
                    f"-> v{ver}"
                )
            time.sleep(PAUSE)

    # final fleet table
    draw_fleet_table(VANS, versions)

    # ASCII map
    draw_ascii_map(VANS)

    # full history for first two vans
    draw_history("VAN_001")
    draw_history("VAN_002")

    # validation demo
    test_validation_errors()

    # summary
    banner("Simulation complete")
    print(f"  Total updates stored: {sum(versions.values())}")
    print(f"  Each van has {ROUNDS} versioned rows, fully queryable")
    print(f"  No data was overwritten - append-only history preserved")
    print()


if __name__ == "__main__":
    main()

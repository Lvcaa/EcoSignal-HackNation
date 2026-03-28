#!/usr/bin/env python3
"""
GTFS-Realtime → van_management: invio posizioni come truck telemetry.

Default: POST /api/v1/trucks/batch (fino a 500 aggiornamenti per richiesta, doc API).
Opzione: --mode single → POST /api/v1/trucks/update per ogni veicolo (parallelo).

Variabili d'ambiente:
  VAN_BASE_URL, COMPANY_ID, WASTE_TYPE, TRUCK_ID_PREFIX, GTFS_RT_URL,
  POLL_INTERVAL_SEC, POST_WORKERS (solo --mode single),
  MIN_SEND_INTERVAL_SEC, MIN_SEND_METERS, MAX_POSTS_PER_CYCLE

Esempi:
  python3 forward_positions.py
  python3 forward_positions.py --mode single --dry-run --once --max-vehicles 5
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from google.transit import gtfs_realtime_pb2

DEFAULT_VAN_BASE_URL = "https://dayana-nonfulminating-novella.ngrok-free.dev"
DEFAULT_GTFS_URL = (
    "https://romamobilita.it/sites/default/files/"
    "rome_rtgtfs_vehicle_positions_feed.pb"
)
DEFAULT_COMPANY_ID = "ROMA_GTFS"

API_PREFIX = "/api/v1/trucks"
UPDATE_PATH = f"{API_PREFIX}/update"
BATCH_PATH = f"{API_PREFIX}/batch"
BATCH_MAX_ITEMS = 500

# Doc: scripted access deve usare header letterale "true"
JSON_HEADERS = {
    "ngrok-skip-browser-warning": "true",
    "Content-Type": "application/json",
}


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def iso_utc(ts: float | None) -> str:
    if ts is None or ts <= 0:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class VehicleState:
    lat: float
    lon: float
    timestamp: float


@dataclass
class LastSent:
    lat: float
    lon: float
    monotonic_time: float


def fetch_feed(url: str) -> gtfs_realtime_pb2.FeedMessage:
    resp = requests.get(url, timeout=45)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def iter_vehicle_positions(
    feed: gtfs_realtime_pb2.FeedMessage,
) -> list[tuple[str, str, str, float, float, float]]:
    out: list[tuple[str, str, str, float, float, float]] = []
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        v = entity.vehicle
        if not v.HasField("position"):
            continue
        lat = v.position.latitude
        lon = v.position.longitude
        pos_ts = float(v.timestamp) if v.HasField("timestamp") else 0.0
        vid = v.vehicle.id if v.HasField("vehicle") else entity.id
        trip_id = v.trip.trip_id if v.HasField("trip") else ""
        route_id = v.trip.route_id if v.HasField("trip") else ""
        out.append((vid, trip_id, route_id, lat, lon, pos_ts))
    return out


def make_truck_id(prefix: str, vehicle_id: str) -> str:
    raw = f"{prefix}{vehicle_id}".strip()
    return raw[:64]


def motion_extra(
    prev: VehicleState | None,
    lat: float,
    lon: float,
    pos_ts: float,
    stop_speed_kmh: float,
    min_move_m: float,
) -> dict[str, Any]:
    now = time.time()
    if prev is None:
        return {
            "distance_meters_since_last": 0.0,
            "speed_kmh": None,
            "is_stopped": None,
        }
    dist = haversine_meters(prev.lat, prev.lon, lat, lon)
    dt = pos_ts - prev.timestamp if pos_ts > 0 else now - prev.timestamp
    if dt <= 0:
        speed_kmh = 0.0
    else:
        speed_kmh = (dist / dt) * 3.6
    stopped = (speed_kmh < stop_speed_kmh) or (
        dist < min_move_m and speed_kmh < stop_speed_kmh * 2
    )
    return {
        "distance_meters_since_last": round(dist, 2),
        "speed_kmh": round(speed_kmh, 2) if speed_kmh is not None else None,
        "is_stopped": stopped,
    }


def should_send_update(
    last: LastSent | None,
    lat: float,
    lon: float,
    now_mono: float,
    min_seconds: float,
    min_meters: float,
) -> bool:
    if last is None:
        return True
    elapsed = now_mono - last.monotonic_time
    dist = haversine_meters(last.lat, last.lon, lat, lon)
    time_ok = min_seconds <= 0 or elapsed >= min_seconds
    move_ok = min_meters <= 0 or dist >= min_meters
    return time_ok and move_ok


def build_single_update_body(
    truck_id: str,
    waste_type: str,
    lat: float,
    lon: float,
    position_ts: float,
) -> dict[str, Any]:
    return {
        "truck_id": truck_id,
        "waste_type": waste_type,
        "current_position": {
            "latitude": lat,
            "longitude": lon,
            "timestamp": iso_utc(position_ts if position_ts > 0 else None),
        },
    }


def truncate_err(text: str, limit: int = 400) -> str:
    t = text.replace("\n", " ").strip()
    return t if len(t) <= limit else t[: limit - 3] + "..."


def post_json(url: str, payload: dict[str, Any], timeout: float) -> tuple[bool, str]:
    try:
        r = requests.post(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=JSON_HEADERS,
            timeout=timeout,
        )
        if r.status_code in (200, 201):
            return True, ""
        preview_limit = 800 if r.status_code >= 500 else 400
        return False, f"HTTP {r.status_code} {truncate_err(r.text, preview_limit)}"
    except requests.RequestException as e:
        return False, str(e)


def chunk_updates(
    items: list[dict[str, Any]], max_size: int
) -> list[list[dict[str, Any]]]:
    return [items[i : i + max_size] for i in range(0, len(items), max_size)]


def run(
    base_url: str,
    company_id: str,
    ingest_mode: str,
    waste_type: str,
    truck_prefix: str,
    gtfs_url: str,
    interval_sec: float,
    workers: int,
    stop_speed_kmh: float,
    min_move_m: float,
    dry_run: bool,
    max_vehicles: int | None,
    timeout: float,
    once: bool,
    min_seconds_between_sends: float,
    min_meters_between_sends: float,
    max_updates_per_cycle: int | None,
    batch_max: int,
) -> None:
    base = base_url.rstrip("/")
    update_url = f"{base}{UPDATE_PATH}"
    batch_url = f"{base}{BATCH_PATH}"
    states: dict[str, VehicleState] = {}
    last_sent: dict[str, LastSent] = {}
    cap = min(batch_max, BATCH_MAX_ITEMS)

    while True:
        t0 = time.perf_counter()
        now_mono = time.monotonic()
        try:
            feed = fetch_feed(gtfs_url)
            positions = iter_vehicle_positions(feed)
            if max_vehicles is not None:
                positions = positions[:max_vehicles]

            tasks: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
            skipped = 0
            for vid, _trip, _route, lat, lon, pos_ts in positions:
                prev = states.get(vid)
                truck_id = make_truck_id(truck_prefix, vid)
                extra = motion_extra(prev, lat, lon, pos_ts, stop_speed_kmh, min_move_m)
                body = build_single_update_body(truck_id, waste_type, lat, lon, pos_ts)
                states[vid] = VehicleState(
                    lat=lat,
                    lon=lon,
                    timestamp=pos_ts if pos_ts > 0 else time.time(),
                )

                ls = last_sent.get(vid)
                if not should_send_update(
                    ls, lat, lon, now_mono, min_seconds_between_sends, min_meters_between_sends
                ):
                    skipped += 1
                    continue

                tasks.append((vid, body, extra))

            if max_updates_per_cycle is not None and len(tasks) > max_updates_per_cycle:
                tasks.sort(key=lambda x: x[0])
                overflow = len(tasks) - max_updates_per_cycle
                tasks = tasks[:max_updates_per_cycle]
                skipped += overflow

            if dry_run:
                if ingest_mode == "batch":
                    updates = [t[1] for t in tasks]
                    batches = chunk_updates(updates, cap)
                    for i, batch in enumerate(batches):
                        payload = {"company_id": company_id, "updates": batch}
                        line = {
                            "would_post_to": batch_url,
                            "batch_index": i + 1,
                            "batches_total": len(batches),
                            "body": payload,
                            "motion_debug_note": "omesso in batch dry-run (per veicolo in tasks)",
                        }
                        print(json.dumps(line, ensure_ascii=False), flush=True)
                    for vid, body, _extra in tasks:
                        lat = body["current_position"]["latitude"]
                        lon = body["current_position"]["longitude"]
                        last_sent[vid] = LastSent(lat, lon, time.monotonic())
                else:
                    for vid, body, extra in tasks:
                        line = {
                            "would_post_to": update_url,
                            "body": body,
                            "motion_debug": extra,
                        }
                        print(json.dumps(line, ensure_ascii=False), flush=True)
                        lat = body["current_position"]["latitude"]
                        lon = body["current_position"]["longitude"]
                        last_sent[vid] = LastSent(lat, lon, time.monotonic())
                if skipped or tasks:
                    print(
                        f"(dry-run) aggiornamenti simulati: {len(tasks)}, saltati: {skipped}",
                        file=sys.stderr,
                    )
            elif ingest_mode == "batch":
                updates = [t[1] for t in tasks]
                vids_order = [t[0] for t in tasks]
                if not updates:
                    print(f"OK: batch 0 aggiornamenti (saltati {skipped})", flush=True)
                else:
                    batches = chunk_updates(updates, cap)
                    # stesso spezzamento per vids
                    vid_chunks: list[list[str]] = []
                    off = 0
                    for b in batches:
                        n = len(b)
                        vid_chunks.append(vids_order[off : off + n])
                        off += n

                    http_errs = 0
                    total_ok_batches = 0
                    for bi, (batch, vchunk) in enumerate(zip(batches, vid_chunks, strict=True)):
                        payload = {"company_id": company_id, "updates": batch}
                        ok, err = post_json(batch_url, payload, timeout)
                        if ok:
                            total_ok_batches += 1
                            mono = time.monotonic()
                            for vid, upd in zip(vchunk, batch, strict=True):
                                lat = upd["current_position"]["latitude"]
                                lon = upd["current_position"]["longitude"]
                                last_sent[vid] = LastSent(lat, lon, mono)
                        else:
                            http_errs += 1
                            print(
                                f"POST batch {bi + 1}/{len(batches)} fallita: {err}",
                                file=sys.stderr,
                            )
                    elapsed = time.perf_counter() - t0
                    print(
                        f"OK: batch {total_ok_batches}/{len(batches)} richieste HTTP, "
                        f"{len(updates)} aggiornamenti (saltati {skipped}) in {elapsed:.1f}s"
                        + (f", errori HTTP batch: {http_errs}" if http_errs else ""),
                        flush=True,
                    )
            else:
                errors = 0
                with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
                    futs = {
                        ex.submit(post_json, update_url, body, timeout): (vid, body)
                        for vid, body, _ in tasks
                    }
                    for fut in as_completed(futs):
                        vid, body = futs[fut]
                        ok, err = fut.result()
                        if ok:
                            lat = body["current_position"]["latitude"]
                            lon = body["current_position"]["longitude"]
                            last_sent[vid] = LastSent(lat, lon, time.monotonic())
                        else:
                            errors += 1
                            print(f"POST fallita {vid}: {err}", file=sys.stderr)
                elapsed = time.perf_counter() - t0
                print(
                    f"OK: POST singoli {len(tasks)} (saltati {skipped}) in {elapsed:.1f}s"
                    + (f", errori: {errors}" if errors else ""),
                    flush=True,
                )
        except requests.RequestException as e:
            print(f"Errore HTTP (feed o API): {e}", file=sys.stderr)
        except Exception as e:
            print(f"Errore: {e}", file=sys.stderr)

        if once:
            break
        time.sleep(interval_sec)


def main() -> None:
    _max_posts_env = os.environ.get("MAX_POSTS_PER_CYCLE")
    _max_posts_default: int | None
    if _max_posts_env and _max_posts_env.strip():
        _max_posts_default = int(_max_posts_env.strip())
    else:
        _max_posts_default = None

    ap = argparse.ArgumentParser(
        description="GTFS-RT → van_management (batch /update o singoli /update)"
    )
    ap.add_argument(
        "--base-url",
        default=os.environ.get("VAN_BASE_URL", DEFAULT_VAN_BASE_URL),
        help="Base URL API (ngrok o localhost)",
    )
    ap.add_argument(
        "--mode",
        choices=("batch", "single"),
        default=os.environ.get("INGEST_MODE", "batch"),
        help="batch=POST /trucks/batch (default), single=POST /trucks/update per veicolo",
    )
    ap.add_argument(
        "--company-id",
        default=os.environ.get("COMPANY_ID", DEFAULT_COMPANY_ID),
        help="Obbligatorio per --mode batch (campo company_id nel body)",
    )
    ap.add_argument(
        "--batch-size",
        type=int,
        default=min(
            int(os.environ.get("BATCH_CHUNK_SIZE", str(BATCH_MAX_ITEMS))),
            BATCH_MAX_ITEMS,
        ),
        help=f"Max aggiornamenti per richiesta batch (max {BATCH_MAX_ITEMS}, doc API)",
    )
    ap.add_argument(
        "--waste-type",
        default=os.environ.get("WASTE_TYPE", "mixed"),
        choices=("organic", "paper", "plastic", "glass", "mixed"),
    )
    ap.add_argument(
        "--truck-prefix",
        default=os.environ.get("TRUCK_ID_PREFIX", "BUS_"),
        help="Prefisso truck_id (max 64 caratteri totali)",
    )
    ap.add_argument(
        "--url",
        default=os.environ.get("GTFS_RT_URL", DEFAULT_GTFS_URL),
        help="URL feed GTFS-RT .pb",
    )
    ap.add_argument(
        "--interval",
        type=float,
        default=float(os.environ.get("POLL_INTERVAL_SEC", "60")),
        help="Secondi tra un poll e l'altro",
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("POST_WORKERS", "24")),
        help="Solo --mode single: POST paralleli",
    )
    ap.add_argument("--stop-speed", type=float, default=3.0)
    ap.add_argument("--min-move", type=float, default=5.0)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-vehicles", type=int, default=None)
    ap.add_argument("--once", action="store_true")
    ap.add_argument(
        "--min-send-interval",
        type=float,
        default=float(os.environ.get("MIN_SEND_INTERVAL_SEC", "90")),
        help="Min secondi tra due invii per lo stesso veicolo (0 = off)",
    )
    ap.add_argument(
        "--min-send-meters",
        type=float,
        default=float(os.environ.get("MIN_SEND_METERS", "40")),
        help="Min metri dall'ultimo invio riuscito (0 = off)",
    )
    ap.add_argument(
        "--max-posts-per-cycle",
        type=int,
        default=_max_posts_default,
        help="Dopo i filtri, max aggiornamenti inviati per ciclo (default: nessun tetto)",
    )
    args = ap.parse_args()

    bs = max(1, min(args.batch_size, BATCH_MAX_ITEMS))

    run(
        base_url=args.base_url,
        company_id=args.company_id.strip() or DEFAULT_COMPANY_ID,
        ingest_mode=args.mode,
        waste_type=args.waste_type,
        truck_prefix=args.truck_prefix,
        gtfs_url=args.url,
        interval_sec=args.interval,
        workers=args.workers,
        stop_speed_kmh=args.stop_speed,
        min_move_m=args.min_move,
        dry_run=args.dry_run,
        max_vehicles=args.max_vehicles,
        timeout=args.timeout,
        once=args.once,
        min_seconds_between_sends=args.min_send_interval,
        min_meters_between_sends=args.min_send_meters,
        max_updates_per_cycle=args.max_posts_per_cycle,
        batch_max=bs,
    )


if __name__ == "__main__":
    main()

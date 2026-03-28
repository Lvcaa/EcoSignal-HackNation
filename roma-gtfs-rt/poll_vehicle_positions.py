#!/usr/bin/env python3
"""
Legge il feed GTFS-Realtime open data di Roma (posizioni veicoli) e lo
ripete ogni N secondi. I dati statici (orari) sono in GTFS zip separato.

Fonti ufficiali (Roma Mobilità, aggiornamento feed ~60 s):
  https://romamobilita.it/it/tecnologie/open-data

Feed usati qui:
  - Posizioni veicoli: rome_rtgtfs_vehicle_positions_feed.pb
  - (Opzionale) trip updates / alerts: stessi path con altro nome file.
"""

import argparse
import sys
import time

import requests
from google.transit import gtfs_realtime_pb2

# URL predefinito open data Roma Mobilità
DEFAULT_VEHICLE_POSITIONS_URL = (
    "https://romamobilita.it/sites/default/files/"
    "rome_rtgtfs_vehicle_positions_feed.pb"
)


def fetch_feed(url: str) -> gtfs_realtime_pb2.FeedMessage:
    """Scarica il file .pb e lo decodifica in FeedMessage."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def summarize_positions(feed: gtfs_realtime_pb2.FeedMessage, max_rows: int) -> None:
    """Stampa un riepilogo leggibile (prime N entità con posizione)."""
    n = 0
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        v = entity.vehicle
        if not v.HasField("position"):
            continue
        lat = v.position.latitude
        lon = v.position.longitude
        trip = v.trip.trip_id if v.HasField("trip") else ""
        vid = v.vehicle.id if v.HasField("vehicle") else ""
        print(f"  vehicle_id={vid!r} trip_id={trip!r} lat={lat:.5f} lon={lon:.5f}")
        n += 1
        if n >= max_rows:
            break
    if n == 0:
        print("  (nessuna posizione veicolo nel feed)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Polling GTFS-RT vehicle positions (Roma open data)"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_VEHICLE_POSITIONS_URL,
        help="URL del feed .pb (default: Roma vehicle positions)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=60.0,
        help="Secondi tra una richiesta e la successiva (default: 60, coerente con aggiornamento ~60s)",
    )
    parser.add_argument(
        "--max-print",
        type=int,
        default=5,
        help="Quante posizioni stampare per ciclo (default: 5)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Scarica una sola volta ed esci (utile per test)",
    )
    args = parser.parse_args()

    if args.interval < 10:
        print(
            "Avviso: l'intervallo è molto basso; il feed Roma si aggiorna circa ogni 60 s.",
            file=sys.stderr,
        )

    while True:
        try:
            feed = fetch_feed(args.url)
            ts = feed.header.timestamp if feed.header.timestamp else 0
            print(f"\n--- Feed OK | header.timestamp={ts} | entity count={len(feed.entity)} ---")
            summarize_positions(feed, args.max_print)
            # Qui puoi chiamare il tuo altro sistema, es.:
            # requests.post("http://localhost:8000/ingest", json=payload)
        except Exception as e:
            print(f"Errore: {e}", file=sys.stderr)

        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

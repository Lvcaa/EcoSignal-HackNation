#!/usr/bin/env python3
"""
Seed script: generates 1000 fake users in the Rome area (ZIP 00118–00199)
with realistic action history over the last 30 days.

Outputs SQL to stdout — pipe into psql:
    python scripts/seed_community.py | docker compose exec -T postgres psql -U ecosignal -d ecosignal
"""

import hashlib
import json
import random
import uuid
from datetime import date, datetime, timedelta, timezone

# ── Italian names ────────────────────────────────────────────────
FIRST_NAMES_M = [
    "Marco", "Luca", "Andrea", "Giovanni", "Francesco", "Alessandro",
    "Matteo", "Lorenzo", "Simone", "Davide", "Federico", "Giuseppe",
    "Antonio", "Stefano", "Roberto", "Riccardo", "Tommaso", "Gabriele",
    "Filippo", "Emanuele", "Nicola", "Daniele", "Paolo", "Pietro",
    "Giacomo", "Fabio", "Massimo", "Claudio", "Vincenzo", "Salvatore",
    "Leonardo", "Diego", "Edoardo", "Michele", "Enrico", "Alberto",
    "Carlo", "Mario", "Angelo", "Sergio", "Giorgio", "Gianluca",
    "Cristiano", "Valerio", "Luca", "Dario", "Bruno", "Renato",
    "Elia", "Samuele",
]
FIRST_NAMES_F = [
    "Giulia", "Francesca", "Sara", "Valentina", "Chiara", "Martina",
    "Laura", "Alessia", "Federica", "Elisa", "Silvia", "Anna",
    "Maria", "Paola", "Giorgia", "Elena", "Sofia", "Arianna",
    "Beatrice", "Alice", "Camilla", "Ilaria", "Roberta", "Monica",
    "Claudia", "Daniela", "Serena", "Lucia", "Marta", "Aurora",
    "Greta", "Irene", "Noemi", "Carlotta", "Bianca", "Viviana",
    "Emanuela", "Teresa", "Rosa", "Angela", "Patrizia", "Simona",
    "Cristina", "Barbara", "Michela", "Sabrina", "Raffaella", "Veronica",
    "Eleonora", "Margherita",
]
LAST_NAMES = [
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano",
    "Colombo", "Ricci", "Marino", "Greco", "Bruno", "Gallo",
    "Conti", "De Luca", "Mancini", "Costa", "Giordano", "Rizzo",
    "Lombardi", "Moretti", "Barbieri", "Fontana", "Santoro", "Mariani",
    "Rinaldi", "Caruso", "Ferrara", "Galli", "Martini", "Leone",
    "Longo", "Gentile", "Martinelli", "Vitale", "Lombardo", "Serra",
    "Coppola", "De Santis", "D'Angelo", "Marchetti", "Parisi", "Villa",
    "Conte", "Ferraro", "Ferri", "Fabbri", "Bianco", "Marini",
    "Grasso", "Valentini", "Messina", "Sala", "De Angelis", "Gatti",
    "Pellegrini", "Palumbo", "Sanna", "Farina", "Rizzi", "Monti",
]

TRANSPORT_MODES = ["car", "transit", "bike", "walk", "mixed"]
TRANSPORT_WEIGHTS = [0.35, 0.30, 0.15, 0.10, 0.10]
DIET_TYPES = ["meat_daily", "meat_weekly", "vegetarian", "vegan"]
DIET_WEIGHTS = [0.30, 0.35, 0.25, 0.10]
HOME_TYPES = ["apartment", "house"]
HOME_WEIGHTS = [0.75, 0.25]  # Rome is mostly apartments
PET_TYPES = ["dog", "cat", "small_animal", "none"]

# Action catalogue (from catalogue.json)
ACTIONS = [
    ("transport_01", "transport", 4.2),
    ("transport_02", "transport", 5.0),
    ("transport_03", "transport", 3.5),
    ("transport_04", "transport", 1.8),
    ("food_01", "food", 3.0),
    ("food_02", "food", 1.5),
    ("food_03", "food", 2.5),
    ("food_04", "food", 5.5),
    ("home_01", "home", 3.8),
    ("home_02", "home", 0.8),
    ("home_03", "home", 1.2),
    ("home_04", "home", 4.5),
    ("community_01", "community", 2.0),
    ("community_02", "community", 1.0),
    ("community_03", "community", 0.5),
]

CHALLENGES = ["no_car_wednesday", "meat_free_week", "energy_saver", "local_shopping"]

ACTION_TYPES_FOR_LOGS = ["meal", "trip", "grocery", "clothing", "appliance"]

MEAL_DESCRIPTIONS = [
    "Pasta al pomodoro con basilico fresco",
    "Insalata mista con tonno e olive",
    "Risotto ai funghi porcini",
    "Pizza margherita fatta in casa",
    "Minestrone di verdure di stagione",
    "Petto di pollo alla griglia con contorno",
    "Spaghetti alle vongole",
    "Lasagna vegetariana",
    "Zuppa di lenticchie rosse",
    "Burger di ceci con insalata",
    "Carbonara tradizionale",
    "Polpette di melanzane al forno",
    "Parmigiana di melanzane",
    "Cous cous con verdure grigliate",
    "Frittata di zucchine e patate",
]

TRIP_DESCRIPTIONS = [
    "Tragitto casa-lavoro in metro",
    "Spostamento in bici al supermercato",
    "Passeggiata al parco",
    "Bus per il centro storico",
    "Carpooling con colleghi",
    "Tragitto in auto al centro commerciale",
    "Tram per l'ufficio",
    "Scooter elettrico condiviso",
    "Camminata per commissioni",
    "Treno regionale per gita fuori porta",
]

GROCERY_DESCRIPTIONS = [
    "Spesa settimanale al mercato rionale",
    "Frutta e verdura biologica dal contadino",
    "Prodotti sfusi al negozio zero waste",
    "Spesa al supermercato con borsa riutilizzabile",
    "Acquisto prodotti locali e di stagione",
]

# ── Rome coordinates bounding box ────────────────────────────────
ROME_LAT_MIN, ROME_LAT_MAX = 41.80, 41.97
ROME_LON_MIN, ROME_LON_MAX = 12.38, 12.58

# ── Dates ────────────────────────────────────────────────────────
TODAY = date(2026, 3, 29)
SEED_START = TODAY - timedelta(days=30)
ROME_TZ = timezone(timedelta(hours=1))

NUM_USERS = 1000

random.seed(42)


def sql_str(s: str) -> str:
    """Escape single quotes for SQL."""
    return s.replace("'", "''")


def fake_hash(password: str) -> str:
    """Fake bcrypt-style hash (not real bcrypt, just for seed data)."""
    h = hashlib.sha256(password.encode()).hexdigest()[:60]
    return f"$2b$12${h}{'0' * (53 - len(h))}"


def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def generate_users():
    """Generate 1000 user records."""
    users = []
    emails_seen = set()

    for i in range(NUM_USERS):
        uid = str(uuid.uuid4())
        is_female = random.random() < 0.5
        first = random.choice(FIRST_NAMES_F if is_female else FIRST_NAMES_M)
        last = random.choice(LAST_NAMES)
        display_name = f"{first} {last}"

        # Unique email
        base_email = f"{first.lower()}.{last.lower().replace(' ', '').replace(chr(39), '')}".replace(" ", "")
        email = f"{base_email}{i}@ecosignal.example.com"
        while email in emails_seen:
            email = f"{base_email}{i}{random.randint(100,999)}@ecosignal.example.com"
        emails_seen.add(email)

        zip_code = f"00{random.randint(118, 199)}"
        lat = round(random.uniform(ROME_LAT_MIN, ROME_LAT_MAX), 6)
        lon = round(random.uniform(ROME_LON_MIN, ROME_LON_MAX), 6)
        transport = weighted_choice(TRANSPORT_MODES, TRANSPORT_WEIGHTS)
        diet = weighted_choice(DIET_TYPES, DIET_WEIGHTS)
        home = weighted_choice(HOME_TYPES, HOME_WEIGHTS)
        home_size = random.randint(30, 180) if home == "apartment" else random.randint(80, 300)
        commute_days = random.randint(0, 5)
        has_pets = random.random() < 0.35
        pet_type = random.choice(["dog", "cat", "small_animal"]) if has_pets else "none"
        pet_count = random.randint(1, 3) if has_pets else 0

        # Users created over the last 2 months
        created_days_ago = random.randint(1, 60)
        created_at = datetime(2026, 3, 29, tzinfo=ROME_TZ) - timedelta(
            days=created_days_ago,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        users.append({
            "id": uid,
            "email": email,
            "display_name": display_name,
            "hashed_password": fake_hash("seedpass123"),
            "zip_code": zip_code,
            "address": f"Via Roma {random.randint(1, 300)}, Roma",
            "latitude": lat,
            "longitude": lon,
            "transport_mode": transport,
            "diet_type": diet,
            "home_type": home,
            "home_size_sqm": home_size,
            "commute_days_per_week": commute_days,
            "has_pets": has_pets,
            "pet_type": pet_type,
            "pet_count": pet_count,
            "created_at": created_at,
        })

    return users


def generate_action_data(users):
    """Generate action completions, logs, streaks, footprints, and challenge participation."""
    completions = []
    logs = []
    streaks = {}
    footprints = []  # anonymized per-zip
    challenge_parts = []
    footprint_refs = []

    # Track per-zip weekly CO2 for anonymized footprints
    zip_week_co2 = {}  # {(zip, week, year): [co2_values]}

    for user in users:
        uid = user["id"]
        user_created = user["created_at"].date()
        start_date = max(SEED_START, user_created)

        if start_date >= TODAY:
            continue

        # Each user completes 0-4 actions per day, with some days off
        activity_level = random.uniform(0.3, 0.9)  # probability of being active on a given day
        total_completions = 0
        last_action_date = None
        current_streak = 0
        prev_date_active = None
        weekly_co2 = {}  # {(week, year): total_co2}

        day = start_date
        while day <= TODAY:
            if random.random() < activity_level:
                # Pick 1-4 actions for this day
                num_actions = random.randint(1, min(4, len(ACTIONS)))
                day_actions = random.sample(ACTIONS, num_actions)

                completed_at = datetime(
                    day.year, day.month, day.day,
                    random.randint(7, 22), random.randint(0, 59),
                    tzinfo=ROME_TZ,
                )

                for action_id, category, co2_saving in day_actions:
                    comp_id = str(uuid.uuid4())
                    completions.append({
                        "id": comp_id,
                        "user_id": uid,
                        "action_id": action_id,
                        "completed_at": completed_at.isoformat(),
                        "date_rome": day.isoformat(),
                    })
                    total_completions += 1

                # Also generate 0-2 action logs (meal/trip/grocery tracking)
                num_logs = random.randint(0, 2)
                for _ in range(num_logs):
                    log_type = random.choice(ACTION_TYPES_FOR_LOGS)
                    if log_type == "meal":
                        desc = random.choice(MEAL_DESCRIPTIONS)
                        co2 = round(random.uniform(0.5, 4.0), 2)
                    elif log_type == "trip":
                        desc = random.choice(TRIP_DESCRIPTIONS)
                        co2 = round(random.uniform(0.2, 8.0), 2)
                    elif log_type == "grocery":
                        desc = random.choice(GROCERY_DESCRIPTIONS)
                        co2 = round(random.uniform(1.0, 6.0), 2)
                    elif log_type == "clothing":
                        desc = "Acquisto abbigliamento"
                        co2 = round(random.uniform(2.0, 15.0), 2)
                    else:  # appliance
                        desc = "Sondaggio elettrodomestici settimanale"
                        co2 = round(random.uniform(1.0, 5.0), 2)

                    log_created = datetime(
                        day.year, day.month, day.day,
                        random.randint(8, 21), random.randint(0, 59),
                        tzinfo=ROME_TZ,
                    )
                    logs.append({
                        "id": str(uuid.uuid4()),
                        "user_id": uid,
                        "action_type": log_type,
                        "description": desc,
                        "co2_delta_kg": co2,
                        "created_at": log_created.isoformat(),
                    })

                    # Accumulate weekly CO2
                    iso = day.isocalendar()
                    wk_key = (iso.week, iso.year)
                    weekly_co2.setdefault(wk_key, 0.0)
                    weekly_co2[wk_key] += co2

                # Streak tracking
                if prev_date_active and (day - prev_date_active).days == 1:
                    current_streak += 1
                elif prev_date_active and (day - prev_date_active).days > 1:
                    current_streak = 1
                else:
                    current_streak = 1

                last_action_date = day
                prev_date_active = day

            day += timedelta(days=1)

        # Save streak
        if total_completions > 0:
            streaks[uid] = {
                "user_id": uid,
                "current_streak": current_streak,
                "last_action_date": last_action_date.isoformat() if last_action_date else None,
                "total_completions": total_completions,
            }

        # Anonymized footprints per week
        for (wk, yr), co2_total in weekly_co2.items():
            # Baseline weekly CO2 based on user profile
            baseline = 30.0  # average Italian ~30 kg CO2/week lifestyle
            if user["diet_type"] == "vegan":
                baseline -= 5
            elif user["diet_type"] == "vegetarian":
                baseline -= 3
            if user["transport_mode"] in ("bike", "walk"):
                baseline -= 4
            elif user["transport_mode"] == "transit":
                baseline -= 2

            actual_co2 = round(baseline + random.uniform(-5, 5) - co2_total * 0.3, 2)
            actual_co2 = max(5.0, actual_co2)

            fp_id = str(uuid.uuid4())
            footprints.append({
                "id": fp_id,
                "zip_code": user["zip_code"],
                "kg_co2_week": actual_co2,
                "week_number": wk,
                "year": yr,
            })

            zk = (user["zip_code"], wk, yr)
            zip_week_co2.setdefault(zk, []).append(actual_co2)

        # Footprint ref (latest week)
        if weekly_co2:
            latest_wk = max(weekly_co2.keys())
            latest_co2 = weekly_co2[latest_wk]
            baseline = 30.0
            ref_co2 = round(baseline + random.uniform(-5, 5) - latest_co2 * 0.3, 2)
            ref_co2 = max(5.0, ref_co2)
            footprint_refs.append({
                "user_id": uid,
                "display_name": user["display_name"],
                "zip_code": user["zip_code"],
                "last_kg_co2": ref_co2,
            })

        # Challenge participation (~40% chance per week)
        for (wk, yr) in weekly_co2.keys():
            if random.random() < 0.40:
                challenge_id = CHALLENGES[wk % 4]
                challenge_parts.append({
                    "id": str(uuid.uuid4()),
                    "challenge_id": challenge_id,
                    "user_id": uid,
                    "week_number": wk,
                    "year": yr,
                })

    return completions, logs, streaks, footprints, footprint_refs, challenge_parts


def emit_sql(users, completions, logs, streaks, footprints, footprint_refs, challenge_parts):
    """Output all INSERT statements."""
    print("-- EcoSignal Community Seed Data")
    print("-- Generated: 1000 users in Rome area with 30 days of activity")
    print("BEGIN;")
    print()
    # Add display_name column to user_footprint_refs if it doesn't exist
    print("ALTER TABLE user_footprint_refs ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);")
    print()

    # ── Users ────────────────────────────────────────────────────
    print("-- Users")
    for u in users:
        print(
            f"INSERT INTO users (id, email, display_name, hashed_password, "
            f"zip_code, address, latitude, longitude, transport_mode, diet_type, "
            f"home_type, home_size_sqm, commute_days_per_week, has_pets, pet_type, "
            f"pet_count, created_at, updated_at) VALUES ("
            f"'{u['id']}', '{sql_str(u['email'])}', '{sql_str(u['display_name'])}', "
            f"'{u['hashed_password']}', '{u['zip_code']}', '{sql_str(u['address'])}', "
            f"{u['latitude']}, {u['longitude']}, '{u['transport_mode']}', "
            f"'{u['diet_type']}', '{u['home_type']}', {u['home_size_sqm']}, "
            f"{u['commute_days_per_week']}, {str(u['has_pets']).lower()}, "
            f"'{u['pet_type']}', {u['pet_count']}, "
            f"'{u['created_at'].isoformat()}', '{u['created_at'].isoformat()}'"
            f") ON CONFLICT (email) DO NOTHING;"
        )
    print()

    # ── Action Completions ───────────────────────────────────────
    print("-- Action Completions")
    for c in completions:
        print(
            f"INSERT INTO action_completions (id, user_id, action_id, completed_at, date_rome) VALUES ("
            f"'{c['id']}', '{c['user_id']}', '{c['action_id']}', "
            f"'{c['completed_at']}', '{c['date_rome']}'"
            f") ON CONFLICT DO NOTHING;"
        )
    print()

    # ── Action Logs ──────────────────────────────────────────────
    print("-- Action Logs")
    for l in logs:
        print(
            f"INSERT INTO action_logs (id, user_id, action_type, description, "
            f"co2_delta_kg, created_at) VALUES ("
            f"'{l['id']}', '{l['user_id']}', '{l['action_type']}', "
            f"'{sql_str(l['description'])}', {l['co2_delta_kg']}, "
            f"'{l['created_at']}'"
            f") ON CONFLICT DO NOTHING;"
        )
    print()

    # ── User Streaks ─────────────────────────────────────────────
    print("-- User Streaks")
    for uid, s in streaks.items():
        last_date = f"'{s['last_action_date']}'" if s["last_action_date"] else "NULL"
        print(
            f"INSERT INTO user_streaks (user_id, current_streak, last_action_date, "
            f"total_completions) VALUES ("
            f"'{s['user_id']}', {s['current_streak']}, {last_date}, "
            f"{s['total_completions']}"
            f") ON CONFLICT (user_id) DO UPDATE SET "
            f"current_streak = EXCLUDED.current_streak, "
            f"last_action_date = EXCLUDED.last_action_date, "
            f"total_completions = EXCLUDED.total_completions;"
        )
    print()

    # ── Anonymized Footprints ────────────────────────────────────
    print("-- Anonymized Footprints")
    for f in footprints:
        print(
            f"INSERT INTO anonymized_footprints (id, zip_code, kg_co2_week, "
            f"week_number, year) VALUES ("
            f"'{f['id']}', '{f['zip_code']}', {f['kg_co2_week']}, "
            f"{f['week_number']}, {f['year']}"
            f") ON CONFLICT DO NOTHING;"
        )
    print()

    # ── User Footprint Refs ──────────────────────────────────────
    print("-- User Footprint Refs")
    for r in footprint_refs:
        print(
            f"INSERT INTO user_footprint_refs (user_id, display_name, zip_code, last_kg_co2) VALUES ("
            f"'{r['user_id']}', '{sql_str(r['display_name'])}', '{r['zip_code']}', {r['last_kg_co2']}"
            f") ON CONFLICT (user_id) DO UPDATE SET "
            f"display_name = EXCLUDED.display_name, "
            f"zip_code = EXCLUDED.zip_code, "
            f"last_kg_co2 = EXCLUDED.last_kg_co2;"
        )
    print()

    # ── Challenge Participants ───────────────────────────────────
    print("-- Challenge Participants")
    for cp in challenge_parts:
        print(
            f"INSERT INTO challenge_participants (id, challenge_id, user_id, "
            f"week_number, year) VALUES ("
            f"'{cp['id']}', '{cp['challenge_id']}', '{cp['user_id']}', "
            f"{cp['week_number']}, {cp['year']}"
            f") ON CONFLICT DO NOTHING;"
        )
    print()

    print("COMMIT;")


def main():
    import sys
    print(f"-- Generating {NUM_USERS} users...", file=sys.stderr)
    users = generate_users()

    print("-- Generating action history (30 days)...", file=sys.stderr)
    completions, logs, streaks, footprints, footprint_refs, challenge_parts = generate_action_data(users)

    print(f"-- Users: {len(users)}", file=sys.stderr)
    print(f"-- Action completions: {len(completions)}", file=sys.stderr)
    print(f"-- Action logs: {len(logs)}", file=sys.stderr)
    print(f"-- User streaks: {len(streaks)}", file=sys.stderr)
    print(f"-- Anonymized footprints: {len(footprints)}", file=sys.stderr)
    print(f"-- Footprint refs: {len(footprint_refs)}", file=sys.stderr)
    print(f"-- Challenge participants: {len(challenge_parts)}", file=sys.stderr)
    print("-- Emitting SQL...", file=sys.stderr)

    emit_sql(users, completions, logs, streaks, footprints, footprint_refs, challenge_parts)

    print("-- Done!", file=sys.stderr)


if __name__ == "__main__":
    main()

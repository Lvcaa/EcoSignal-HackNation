import logging
import random
import time
import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.report import Report, ReportStatus
from app.repositories.report_repository import ReportRepository

logger = logging.getLogger(__name__)

ROME_LAT_MIN, ROME_LAT_MAX = 41.82, 41.98
ROME_LNG_MIN, ROME_LNG_MAX = 12.40, 12.56

FALLBACK_PHOTOS = [
    "https://images.unsplash.com/photo-1605600659908-0ef719419d41?w=400",
    "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=400",
    "https://images.unsplash.com/photo-1604187351574-c75ca79f5807?w=400",
    "https://images.unsplash.com/photo-1562077772-3bd90f555678?w=400",
    "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400",
    "https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?w=400",
    "https://images.unsplash.com/photo-1503596476-1c12a8ba09a9?w=400",
    "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=400",
]

CACHE_TTL_SECONDS = 5


@dataclass
class _CachedReport:
    report: Report
    ts: float


_cache: _CachedReport | None = None


def _random_coords() -> tuple[float, float]:
    lat = random.uniform(ROME_LAT_MIN, ROME_LAT_MAX)
    lng = random.uniform(ROME_LNG_MIN, ROME_LNG_MAX)
    return round(lat, 6), round(lng, 6)


def _reverse_geocode(lat: float, lng: float) -> str:
    """Nominatim reverse geocoding — best effort, fallback to coords string."""
    try:
        resp = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lng,
                "format": "jsonv2",
                "addressdetails": 1,
                "zoom": 18,
            },
            headers={"User-Agent": "EcoSignal/1.0"},
            timeout=4.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("display_name", f"{lat}, {lng}")
    except Exception:
        logger.warning("Reverse geocoding failed for (%s, %s)", lat, lng)
        return f"{lat}, {lng}"


def _fetch_photo() -> str:
    """Try Unsplash random photo, fallback to static list."""
    access_key = settings.UNSPLASH_ACCESS_KEY
    if access_key:
        try:
            resp = httpx.get(
                "https://api.unsplash.com/photos/random",
                params={"query": "trash bin full", "orientation": "squarish"},
                headers={"Authorization": f"Client-ID {access_key}"},
                timeout=4.0,
            )
            resp.raise_for_status()
            data = resp.json()
            url = data.get("urls", {}).get("regular")
            if url:
                return url
        except Exception:
            logger.warning("Unsplash API call failed, using fallback")
    return random.choice(FALLBACK_PHOTOS)


class ReportService:
    def __init__(self, db: Session) -> None:
        self.repo = ReportRepository(db)

    def generate_random(self) -> Report:
        global _cache
        now = time.monotonic()
        if _cache is not None and (now - _cache.ts) < CACHE_TTL_SECONDS:
            existing = self.repo.get_by_id(_cache.report.id)
            if existing is not None:
                return existing
            stored = self.repo.create(
                Report(
                    id=_cache.report.id,
                    user_id=_cache.report.user_id,
                    bin_id=_cache.report.bin_id,
                    lat=_cache.report.lat,
                    lng=_cache.report.lng,
                    address=_cache.report.address,
                    photo=_cache.report.photo,
                    status=_cache.report.status,
                    xp=_cache.report.xp,
                )
            )
            return stored

        lat, lng = _random_coords()
        address = _reverse_geocode(lat, lng)
        photo = _fetch_photo()

        report = Report(
            id=str(uuid.uuid4()),
            user_id="u_system",
            bin_id=f"bin_{random.randint(1000, 9999)}",
            lat=lat,
            lng=lng,
            address=address,
            photo=photo,
            status=ReportStatus.SENT,
            xp=10,
        )
        stored = self.repo.create(report)
        _cache = _CachedReport(report=stored, ts=now)
        logger.info("Random report %s created at (%s, %s)", stored.id, lat, lng)
        return stored

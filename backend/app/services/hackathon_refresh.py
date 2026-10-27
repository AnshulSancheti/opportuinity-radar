"""Periodic freshness checks for the local API process."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.config import get_settings
from app.database import SessionLocal
from app.models import ScrapeRun
from app.services.hackathon_service import LIVE_SOURCES
from app.services.scraper_control import start_module_scrape
from app.scrapers.runner import load_sources

logger = logging.getLogger(__name__)


def refresh_due(now=None):
    now = now or datetime.now(timezone.utc)
    interval = timedelta(hours=max(1, get_settings().hackathon_refresh_hours))
    enabled = load_sources().get("hackathons", {})
    with SessionLocal() as db:
        for name in LIVE_SOURCES:
            if not enabled.get(name, {}).get("enabled", True):
                continue
            last = db.scalar(select(ScrapeRun).where(ScrapeRun.module == "hackathons", ScrapeRun.source_name == name).order_by(ScrapeRun.started_at.desc()).limit(1))
            if last and last.status == "running" and last.started_at > now - timedelta(minutes=30):
                continue
            checked = (last.finished_at or last.started_at) if last else None
            delay = interval if last and last.status == "success" else timedelta(minutes=15)
            if checked is None or checked < now - delay:
                return True
    return False


async def refresh_loop():
    while True:
        try:
            if await asyncio.to_thread(refresh_due):
                start_module_scrape("hackathons")
        except Exception:
            logger.exception("Hackathon refresh check failed")
        await asyncio.sleep(60)

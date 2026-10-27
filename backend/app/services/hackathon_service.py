from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session
from app.models import Hackathon
from app.services.cleaner import canonicalize_url, clean_text, make_content_hash

LIVE_SOURCES = ("mlh", "devpost")


def discoverable_hackathons(now=None):
    """Read-time filtering avoids showing ended/closed events between refreshes."""
    now = now or datetime.now(timezone.utc)
    return and_(
        Hackathon.status == "active", Hackathon.source_name.in_(LIVE_SOURCES),
        func.coalesce(Hackathon.end_date, Hackathon.registration_deadline, Hackathon.start_date) >= now,
        or_(Hackathon.registration_deadline.is_(None), Hackathon.registration_deadline >= now),
        Hackathon.last_seen_at >= now - timedelta(hours=48),
    )


def upsert_hackathon(db: Session, data: dict) -> str:
    name, url = clean_text(data.get("name")), canonicalize_url(data.get("url"))
    if not name or not url or not data.get("source_event_id") or data.get("source_name") not in LIVE_SOURCES:
        return "skipped"
    # Provider identity survives corrected dates/names; website URLs can be
    # reused by annual editions, so they must not merge independent events.
    content_hash = make_content_hash(data["source_name"], str(data["source_event_id"]))
    existing = db.scalar(select(Hackathon).where(Hackathon.content_hash == content_hash))
    now = datetime.now(timezone.utc)
    end = data.get("end_date") or data.get("registration_deadline") or data.get("start_date")
    if not end:
        return "skipped"
    status = "expired" if end < now else "active"
    values = {key: data.get(key) for key in ("organizer", "mode", "location", "registration_deadline", "start_date", "end_date", "prize_text", "team_size", "eligibility", "application_status")}
    values.update(name=name, url=url, canonical_url=url, source_name=data["source_name"], themes=data.get("themes") or [], description=clean_text(data.get("description")), status=status, last_seen_at=now)
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
        db.commit()
        return "updated"
    db.add(Hackathon(**values, content_hash=content_hash, first_seen_at=now))
    db.commit()
    return "inserted"


def reconcile_hackathon_source(db, source, checked_at):
    # Only called after complete successful source ingestion. Missing events
    # leave discovery but stay addressable by private saved/applied collections.
    db.execute(update(Hackathon).where(Hackathon.source_name == source, Hackathon.last_seen_at < checked_at, Hackathon.status == "active").values(status="unavailable"))
    db.execute(update(Hackathon).where(Hackathon.source_name == source, func.coalesce(Hackathon.end_date, Hackathon.registration_deadline, Hackathon.start_date) < datetime.now(timezone.utc)).values(status="expired"))
    db.commit()

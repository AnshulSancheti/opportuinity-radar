from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Hackathon
from app.services.cleaner import canonicalize_url, clean_text, make_content_hash


def upsert_hackathon(db: Session, data: dict) -> str:
    name = clean_text(data.get("name"))
    if not name:
        return "skipped"

    url = canonicalize_url(data.get("url"))
    content_hash = make_content_hash(
        name,
        data.get("organizer"),
        str(data.get("start_date") or data.get("registration_deadline") or ""),
        url,
    )

    existing = None
    if url:
        existing = db.scalar(select(Hackathon).where(Hackathon.url == url))
    if not existing:
        existing = db.scalar(select(Hackathon).where(Hackathon.content_hash == content_hash))

    now = datetime.now(timezone.utc)
    if existing:
        existing.last_seen_at = now
        existing.status = "active"
        db.commit()
        return "updated"

    hackathon = Hackathon(
        name=name,
        organizer=data.get("organizer"),
        url=url,
        canonical_url=url,
        source_name=data["source_name"],
        mode=data.get("mode"),
        location=data.get("location"),
        registration_deadline=data.get("registration_deadline"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        prize_text=data.get("prize_text"),
        team_size=data.get("team_size"),
        themes=data.get("themes") or [],
        eligibility=data.get("eligibility"),
        application_status=data.get("application_status"),
        description=clean_text(data.get("description")),
        status="active",
        content_hash=content_hash,
        first_seen_at=now,
        last_seen_at=now,
    )
    db.add(hackathon)
    db.commit()
    return "inserted"

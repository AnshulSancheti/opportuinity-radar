from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job
from app.services.cleaner import canonicalize_url, clean_text, make_content_hash
from app.services.skill_extractor import extract_skills


def upsert_job(db: Session, data: dict) -> str:
    title = clean_text(data.get("title"))
    company = clean_text(data.get("company"))
    if not title or not company:
        return "skipped"

    apply_url = canonicalize_url(data.get("apply_url") or data.get("source_url"))
    source_url = data.get("source_url") or apply_url or ""
    content_hash = make_content_hash(title, company, data.get("source_name"), apply_url)

    existing = db.scalar(select(Job).where(Job.content_hash == content_hash))
    now = datetime.now(timezone.utc)
    description = clean_text(data.get("description"))
    skills = data.get("skills") or extract_skills(description or "")

    if existing:
        existing.last_seen_at = now
        existing.missed_scrape_count = 0
        existing.status = "active"
        existing.title = title
        existing.location = data.get("location")
        existing.remote_type = data.get("remote_type")
        existing.employment_type = data.get("employment_type")
        # Refreshed on update so a rescrape backfills rows that predate
        # experience-level inference instead of leaving them null forever.
        if data.get("experience_level"):
            existing.experience_level = data.get("experience_level")
        if data.get("date_posted"):
            existing.date_posted = data.get("date_posted")
        existing.skills = skills
        if description:
            existing.description = description
            existing.summary = (description[:300] + "...") if len(description) > 300 else description
        db.commit()
        return "updated"

    job = Job(
        title=title,
        company=company,
        location=data.get("location"),
        remote_type=data.get("remote_type"),
        employment_type=data.get("employment_type"),
        experience_level=data.get("experience_level"),
        salary_text=data.get("salary_text"),
        skills=skills,
        description=description,
        summary=(description[:300] + "...") if description and len(description) > 300 else description,
        source_name=data["source_name"],
        source_url=source_url,
        apply_url=apply_url,
        canonical_url=apply_url,
        date_posted=data.get("date_posted"),
        status="active",
        content_hash=content_hash,
        first_seen_at=now,
        last_seen_at=now,
    )
    db.add(job)
    db.commit()
    return "inserted"

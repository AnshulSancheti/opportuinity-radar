from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Hackathon, Job, ScrapeRun


def run_cleanup(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    summary = {"jobs_unknown": 0, "hackathons_expired": 0, "runs_failed": 0}

    stale_jobs = db.scalars(select(Job).where(Job.status == "active")).all()
    for job in stale_jobs:
        if job.last_seen_at and job.last_seen_at < now - timedelta(days=14):
            job.status = "unknown"
            job.missed_scrape_count += 1
            summary["jobs_unknown"] += 1

    expired_hacks = db.scalars(
        select(Hackathon).where(Hackathon.end_date.is_not(None), Hackathon.end_date < now)
    ).all()
    for hack in expired_hacks:
        hack.status = "expired"
        summary["hackathons_expired"] += 1

    stuck = db.scalars(
        select(ScrapeRun).where(
            ScrapeRun.status == "running",
            ScrapeRun.started_at < now - timedelta(hours=2),
        )
    ).all()
    for run in stuck:
        run.status = "failed"
        run.error_message = "Orphaned run timed out"
        run.finished_at = now
        summary["runs_failed"] += 1

    db.commit()
    return summary


def main() -> None:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        result = run_cleanup(db)
        print("Cleanup complete:", result)
    finally:
        db.close()


if __name__ == "__main__":
    main()

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.hackathon_service import discoverable_hackathons, LIVE_SOURCES
from app.models import ScrapeRun
from app.config import get_settings
from app.models import Hackathon
from app.schemas import HackathonResponse, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[HackathonResponse])
def list_hackathons(
    db: Session = Depends(get_db),
    q: str | None = None,
    mode: str | None = None,
    theme: str | None = None,
    source: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[HackathonResponse]:
    query = select(Hackathon).where(discoverable_hackathons())
    if q:
        query = query.where(
            or_(Hackathon.name.ilike(f"%{q}%"), Hackathon.organizer.ilike(f"%{q}%"))
        )
    if source:
        query = query.where(Hackathon.source_name == source)
    if mode:
        query = query.where(Hackathon.mode == mode)
    if theme:
        query = query.where(Hackathon.themes.any(theme))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    hacks = db.scalars(
        query.order_by(
            Hackathon.registration_deadline.asc().nullslast(),
            Hackathon.start_date.asc().nullslast(),
        )
        .offset(offset).limit(limit)
    ).all()
    return PaginatedResponse(
        items=[HackathonResponse.model_validate(h) for h in hacks],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/sources")
def source_status(db: Session = Depends(get_db)):
    result = []
    for name in LIVE_SOURCES:
        last = db.scalar(select(ScrapeRun).where(ScrapeRun.module == "hackathons", ScrapeRun.source_name == name).order_by(ScrapeRun.started_at.desc()).limit(1))
        success = db.scalar(select(func.max(ScrapeRun.finished_at)).where(ScrapeRun.module == "hackathons", ScrapeRun.source_name == name, ScrapeRun.status == "success"))
        result.append({"name": name, "last_success_at": success, "status": last.status if last else "not_run", "error": last.error_message if last and last.status == "failed" else None, "count": db.scalar(select(func.count(Hackathon.id)).where(discoverable_hackathons(), Hackathon.source_name == name)) or 0})
    return {"sources": result, "auto_refresh": get_settings().hackathon_auto_refresh, "refresh_hours": get_settings().hackathon_refresh_hours}


@router.get("/{hackathon_id}", response_model=HackathonResponse)
def get_hackathon(hackathon_id: int, db: Session = Depends(get_db)) -> HackathonResponse:
    hack = db.get(Hackathon, hackathon_id)
    if not hack:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    return HackathonResponse.model_validate(hack)

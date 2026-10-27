from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Hackathon
from app.schemas import HackathonResponse, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[HackathonResponse])
def list_hackathons(
    db: Session = Depends(get_db),
    q: str | None = None,
    mode: str | None = None,
    theme: str | None = None,
    status: str = "active",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[HackathonResponse]:
    query = select(Hackathon).where(Hackathon.status == status)
    if q:
        query = query.where(
            or_(Hackathon.name.ilike(f"%{q}%"), Hackathon.organizer.ilike(f"%{q}%"))
        )
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


@router.get("/{hackathon_id}", response_model=HackathonResponse)
def get_hackathon(hackathon_id: int, db: Session = Depends(get_db)) -> HackathonResponse:
    hack = db.get(Hackathon, hackathon_id)
    if not hack:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    return HackathonResponse.model_validate(hack)

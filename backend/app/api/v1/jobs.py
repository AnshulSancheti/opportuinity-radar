from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, UserAction
from app.schemas import JobResponse, PaginatedResponse
from app.services.job_search import apply_remote_type_filter, build_job_text_conditions

router = APIRouter()


def hidden_job_ids(db: Session) -> set[int]:
    rows = db.scalars(
        select(UserAction.item_id).where(UserAction.item_type == "job", UserAction.action == "hidden")
    ).all()
    return set(rows)


@router.get("", response_model=PaginatedResponse[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    q: str | None = None,
    company: str | None = None,
    location: str | None = None,
    skill: str | None = None,
    remote_type: str | None = None,
    employment_type: str | None = None,
    status: str = "active",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_hidden: bool = False,
) -> PaginatedResponse[JobResponse]:
    query = select(Job).where(Job.status == status)
    if q:
        conditions = build_job_text_conditions(q)
        if conditions:
            query = query.where(or_(*conditions))
    if company:
        query = query.where(Job.company.ilike(f"%{company}%"))
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if skill:
        query = query.where(Job.skills.any(skill))
    if remote_type:
        query = apply_remote_type_filter(query, remote_type)
    if employment_type:
        query = query.where(Job.employment_type.ilike(f"%{employment_type}%"))
    if not include_hidden:
        hidden = hidden_job_ids(db)
        if hidden:
            query = query.where(Job.id.not_in(hidden))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    jobs = db.scalars(
        query.order_by(Job.date_posted.desc().nullslast(), Job.first_seen_at.desc())
        .offset(offset).limit(limit)
    ).all()
    return PaginatedResponse(
        items=[JobResponse.model_validate(j) for j in jobs],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)

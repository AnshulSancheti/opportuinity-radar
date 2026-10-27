from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.stats import verify_admin
from app.config import get_settings
from app.database import get_db
from app.models import CandidateProfile, Job, JobMatch
from app.schemas import (
    CandidateProfileCreate,
    CandidateProfileResponse,
    JobMatchResponse,
    JobResponse,
    MatchRunRequest,
    MatchRunResponse,
    PaginatedResponse,
    RankedJobResponse,
    Verdict,
)
from app.services import job_matcher

router = APIRouter()


@router.get("/status")
def matching_status(db: Session = Depends(get_db)) -> dict:
    """Public. Lets the UI hide the matching surface when it is not configured
    instead of showing controls that return errors."""
    settings = get_settings()
    profile = job_matcher.active_profile(db)
    return {
        "enabled": settings.matching_enabled,
        "model": settings.match_model if settings.matching_enabled else None,
        "has_profile": profile is not None,
        "scored_jobs": db.scalar(select(func.count(JobMatch.id))) or 0,
    }


@router.get("/profile", response_model=CandidateProfileResponse, dependencies=[Depends(verify_admin)])
def get_profile(db: Session = Depends(get_db)) -> CandidateProfileResponse:
    profile = job_matcher.active_profile(db)
    if profile is None:
        raise HTTPException(status_code=404, detail="No active candidate profile")
    return CandidateProfileResponse.model_validate(profile)


@router.put("/profile", response_model=CandidateProfileResponse, dependencies=[Depends(verify_admin)])
def put_profile(body: CandidateProfileCreate, db: Session = Depends(get_db)) -> CandidateProfileResponse:
    """Replace the active profile. Existing verdicts are left in place — they
    record what a past resume scored, and the run endpoint's `rescore` flag is
    the deliberate way to refresh them."""
    for stale in db.scalars(select(CandidateProfile).where(CandidateProfile.is_active)).all():
        stale.is_active = False

    profile = CandidateProfile(
        label=body.label,
        resume_text=body.resume_text,
        preferences=body.preferences,
        is_active=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return CandidateProfileResponse.model_validate(profile)


@router.post("/run", response_model=MatchRunResponse, dependencies=[Depends(verify_admin)])
def run_matching(body: MatchRunRequest, db: Session = Depends(get_db)) -> MatchRunResponse:
    """Admin-only: every job scored is a billed API call."""
    try:
        result = job_matcher.run_matching(db, limit=body.limit, rescore=body.rescore)
    except job_matcher.MatchingDisabled as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MatchRunResponse(**result)


@router.get("/ranked", response_model=PaginatedResponse[RankedJobResponse])
def ranked_jobs(
    db: Session = Depends(get_db),
    min_score: int = Query(0, ge=0, le=100),
    verdict: Verdict | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[RankedJobResponse]:
    """Public. Jobs the agent has scored, best fit first."""
    query = (
        select(Job, JobMatch)
        .join(JobMatch, JobMatch.job_id == Job.id)
        .where(Job.status == "active", JobMatch.score >= min_score)
    )
    if verdict:
        query = query.where(JobMatch.verdict == verdict)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(JobMatch.score.desc(), Job.first_seen_at.desc()).offset(offset).limit(limit)
    ).all()

    return PaginatedResponse(
        items=[
            RankedJobResponse(
                job=JobResponse.model_validate(job),
                match=JobMatchResponse.model_validate(match),
            )
            for job, match in rows
        ],
        limit=limit,
        offset=offset,
        total=total,
    )

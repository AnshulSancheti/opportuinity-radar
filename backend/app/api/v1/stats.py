import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth import current_account
from app.services.hackathon_service import discoverable_hackathons
from app.config import get_settings
from app.database import get_db
from app.models import Article, Hackathon, Job, ScrapeRun, Source, UserAction
from app.schemas import (
    ArticleResponse,
    HackathonResponse,
    JobResponse,
    PaginatedResponse,
    ScrapeRunResponse,
    ScraperRunRequest,
    ScraperRunResponse,
    StatsResponse,
    UserActionCreate,
    UserActionResponse,
)
from app.services.scraper_control import running_modules, start_module_scrape

router = APIRouter()


def verify_admin(x_admin_password: Annotated[str | None, Header()] = None, account=Depends(current_account)) -> None:
    settings = get_settings()
    if settings.admin_password in {"change-me", "password", "admin", ""}:
        raise HTTPException(status_code=503, detail="Configure a strong ADMIN_PASSWORD before using admin controls")
    if not x_admin_password or not hmac.compare_digest(x_admin_password, settings.admin_password):
        raise HTTPException(status_code=401, detail="Invalid admin password")


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    last_run = db.scalar(select(func.max(ScrapeRun.finished_at)).where(ScrapeRun.module.in_(["news", "hackathons"])))
    failed = db.scalar(
        select(func.count(Source.id)).where(Source.consecutive_failures > 0, Source.module.in_(["news", "hackathons"]))
    ) or 0
    return StatsResponse(
        total_articles=db.scalar(select(func.count(Article.id))) or 0,
        total_hackathons=db.scalar(
            select(func.count(Hackathon.id)).where(discoverable_hackathons())
        ) or 0,
        last_scrape_at=last_run,
        failed_sources=failed,
        active_scrapes=running_modules(),
    )


@router.post("/run-scraper", response_model=ScraperRunResponse, dependencies=[Depends(verify_admin)])
def run_scraper(body: ScraperRunRequest) -> ScraperRunResponse:
    if not start_module_scrape(body.module):
        raise HTTPException(status_code=409, detail=f"{body.module} scrape already in progress")
    return ScraperRunResponse(status="started", module=body.module)


@router.get("/scrape-runs", response_model=list[ScrapeRunResponse], dependencies=[Depends(verify_admin)])
def list_scrape_runs(db: Session = Depends(get_db), limit: int = 50) -> list[ScrapeRunResponse]:
    runs = db.scalars(select(ScrapeRun).where(ScrapeRun.module.in_(["news", "hackathons"])).order_by(ScrapeRun.started_at.desc()).limit(limit)).all()
    return [ScrapeRunResponse.model_validate(r) for r in runs]

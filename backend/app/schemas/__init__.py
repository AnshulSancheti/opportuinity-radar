from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

Verdict = Literal["strong", "possible", "weak", "mismatch"]


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    limit: int
    offset: int
    total: int


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str | None
    canonical_url: str | None
    source_name: str
    author: str | None
    published_at: datetime | None
    first_seen_at: datetime
    summary: str | None
    category: str
    tags: list[str]
    score: int | None
    reading_time_minutes: int | None
    image_url: str | None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    location: str | None
    remote_type: str | None
    employment_type: str | None
    experience_level: str | None
    salary_text: str | None
    skills: list[str]
    description: str | None
    summary: str | None
    source_name: str
    source_url: str
    apply_url: str | None
    date_posted: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    status: str


class HackathonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    organizer: str | None
    url: str | None
    source_name: str
    mode: str | None
    location: str | None
    registration_deadline: datetime | None
    start_date: datetime | None
    end_date: datetime | None
    prize_text: str | None
    team_size: str | None
    themes: list[str]
    eligibility: str | None
    application_status: str | None
    description: str | None
    status: str
    first_seen_at: datetime


class UserActionCreate(BaseModel):
    item_type: str
    item_id: int
    action: str


class UserActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_type: str
    item_id: int
    action: str
    created_at: datetime


class AlertRuleCreate(BaseModel):
    name: str
    module: str
    keyword: str | None = None
    source_name: str | None = None
    location: str | None = None
    skill: str | None = None
    category: str | None = None
    delivery_channel: str = "telegram"
    enabled: bool = True


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    module: str
    keyword: str | None
    source_name: str | None
    location: str | None
    skill: str | None
    category: str | None
    delivery_channel: str
    enabled: bool
    created_at: datetime


class ScrapeRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    module: str
    status: str
    items_found: int
    items_inserted: int
    items_updated: int
    items_skipped: int
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class StatsResponse(BaseModel):
    total_articles: int
    total_hackathons: int
    last_scrape_at: datetime | None
    failed_sources: int
    active_scrapes: list[str]


class ScraperRunRequest(BaseModel):
    module: Literal["news", "hackathons"]


class ScraperRunResponse(BaseModel):
    status: str
    module: str


# ── Job matching agent ────────────────────────────────────────────────────────


class MatchAssessment(BaseModel):
    """The schema the model is constrained to return for a single job.

    Field descriptions are part of the prompt — the model reads them, so they
    are written as instructions rather than as documentation for us.
    """

    score: int = Field(
        ge=0,
        le=100,
        description="Fit from 0-100. 80+ means apply now, 60-79 worth a look, "
        "below 40 means the candidate does not meet the bar.",
    )
    verdict: Verdict = Field(description="Bucket matching the score.")
    reasoning: str = Field(
        description="Two or three sentences addressed to the candidate, citing "
        "specifics from both the resume and the posting. No preamble."
    )
    matched_skills: list[str] = Field(
        description="Skills the posting asks for that the resume evidences."
    )
    missing_skills: list[str] = Field(
        description="Skills the posting asks for that the resume does not evidence."
    )
    closing_move: str = Field(
        description="The single highest-leverage thing the candidate could build "
        "or learn to become credible for this role. One concrete, specific "
        "action — name the project or the skill, not a category. If they are "
        "already credible, say so plainly instead of inventing work."
    )


class CandidateProfileCreate(BaseModel):
    resume_text: str = Field(min_length=50)
    label: str = "default"
    preferences: str | None = None


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    resume_text: str
    preferences: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class JobMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    profile_id: int
    score: int
    verdict: str
    reasoning: str
    matched_skills: list[str]
    missing_skills: list[str]
    closing_move: str | None
    model: str
    created_at: datetime


class RankedJobResponse(BaseModel):
    """A job plus its agent verdict, for the ranked jobs view."""

    job: JobResponse
    match: JobMatchResponse


class MatchRunRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=200)
    rescore: bool = Field(
        default=False, description="Re-score jobs that already have a verdict."
    )


class MatchRunResponse(BaseModel):
    scored: int
    skipped: int
    failed: int
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


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
    total_jobs: int
    total_articles: int
    total_hackathons: int
    last_scrape_at: datetime | None
    failed_sources: int
    active_scrapes: list[str]


class ScraperRunRequest(BaseModel):
    module: Literal["news", "jobs", "hackathons"]


class ScraperRunResponse(BaseModel):
    status: str
    module: str

from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.job_service import upsert_job
from app.services.cleaner import clean_text
from app.services.job_search import (
    infer_employment_type,
    infer_experience_level,
    normalize_remote_type,
)


class WorkableScraper(BaseScraper):
    module = "jobs"
    request_delay_ms = 300

    def __init__(self, db: Session, company: str, account_slug: str):
        super().__init__(db)
        self.company = company
        self.account_slug = account_slug
        self.source_name = f"workable:{account_slug}"

    def fetch(self) -> list[dict]:
        url = f"https://apply.workable.com/api/v1/widget/accounts/{self.account_slug}"
        data = self.fetch_url(url).json()
        items = []
        for job in data.get("jobs", []):
            location = job.get("location", {}).get("country") or job.get("city") or ""
            if job.get("location", {}).get("city"):
                location = f"{job['location']['city']}, {location}".strip(", ")
            title = job.get("title")
            items.append({
                "title": title,
                "company": self.company,
                "location": location,
                "remote_type": normalize_remote_type(location, is_remote_flag=bool(job.get("telecommuting"))),
                "employment_type": infer_employment_type(title, job.get("employment_type")),
                "experience_level": infer_experience_level(title, job.get("employment_type")),
                "source_name": self.source_name,
                "source_url": job.get("url") or f"https://apply.workable.com/{self.account_slug}/j/{job.get('shortcode')}",
                "apply_url": job.get("application_url") or job.get("url"),
                "description": clean_text(job.get("description", "")),
            })
        return items

    def save_item(self, item: dict) -> str:
        return upsert_job(self.db, item)

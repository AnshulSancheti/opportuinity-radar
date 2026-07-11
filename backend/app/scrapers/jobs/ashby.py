from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.job_service import upsert_job
from app.services.cleaner import clean_text
from app.services.job_search import infer_employment_type, normalize_remote_type


class AshbyScraper(BaseScraper):
    module = "jobs"
    request_delay_ms = 300

    def __init__(self, db: Session, company: str, board_name: str):
        super().__init__(db)
        self.company = company
        self.board_name = board_name
        self.source_name = f"ashby:{board_name}"

    def fetch(self) -> list[dict]:
        url = (
            f"https://api.ashbyhq.com/posting-api/job-board/{self.board_name}"
            "?includeCompensation=true"
        )
        data = self.fetch_url(url).json()
        items = []
        for job in data.get("jobs", []):
            if not job.get("isListed", True):
                continue
            location = job.get("location", "")
            secondary = job.get("secondaryLocations") or []
            if secondary:
                location = f"{location}, {', '.join(secondary)}"
            title = job.get("title")
            employment = job.get("employmentType")
            remote_type = normalize_remote_type(location, is_remote_flag=bool(job.get("isRemote")))
            comp = job.get("compensation") or {}
            salary = comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary")
            published = None
            if job.get("publishedAt"):
                try:
                    published = datetime.fromisoformat(job["publishedAt"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            items.append({
                "title": title,
                "company": self.company,
                "location": location,
                "remote_type": remote_type,
                "employment_type": infer_employment_type(title, employment),
                "source_name": self.source_name,
                "source_url": job.get("jobUrl"),
                "apply_url": job.get("applyUrl") or job.get("jobUrl"),
                "date_posted": published,
                "salary_text": salary,
                "description": clean_text(job.get("descriptionHtml", "")),
            })
        return items

    def save_item(self, item: dict) -> str:
        return upsert_job(self.db, item)

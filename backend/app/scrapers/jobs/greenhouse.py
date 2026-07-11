from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.job_service import upsert_job
from app.services.job_search import infer_employment_type, normalize_remote_type


class GreenhouseScraper(BaseScraper):
    module = "jobs"
    request_delay_ms = 200

    def __init__(self, db: Session, company: str, board_token: str):
        super().__init__(db)
        self.company = company
        self.board_token = board_token
        self.source_name = f"greenhouse:{board_token}"

    def fetch(self) -> list[dict]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs"
        data = self.fetch_url(url).json()
        items = []
        for job in data.get("jobs", [])[:100]:
            location = job.get("location", {}).get("name") if isinstance(job.get("location"), dict) else job.get("location")
            title = job.get("title")
            items.append({
                "title": title,
                "company": self.company,
                "location": location,
                "remote_type": normalize_remote_type(location),
                "employment_type": infer_employment_type(title),
                "source_name": self.source_name,
                "source_url": job.get("absolute_url"),
                "apply_url": job.get("absolute_url"),
                "date_posted": None,
                "description": None,
            })
        return items

    def save_item(self, item: dict) -> str:
        return upsert_job(self.db, item)

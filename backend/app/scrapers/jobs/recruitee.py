from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.job_service import upsert_job
from app.services.cleaner import clean_text
from app.services.job_search import infer_employment_type, normalize_remote_type


class RecruiteeScraper(BaseScraper):
    module = "jobs"
    request_delay_ms = 300

    def __init__(self, db: Session, company: str, subdomain: str):
        super().__init__(db)
        self.company = company
        self.subdomain = subdomain
        self.source_name = f"recruitee:{subdomain}"

    def fetch(self) -> list[dict]:
        url = f"https://{self.subdomain}.recruitee.com/api/offers"
        data = self.fetch_url(url).json()
        items = []
        for job in data.get("offers", []):
            location = job.get("city") or job.get("country") or job.get("location")
            title = job.get("title")
            employment = job.get("employment_type_code")
            items.append({
                "title": title,
                "company": self.company,
                "location": location,
                "remote_type": normalize_remote_type(location, is_remote_flag=bool(job.get("remote"))),
                "employment_type": infer_employment_type(title, employment),
                "source_name": self.source_name,
                "source_url": job.get("careers_url") or job.get("url"),
                "apply_url": job.get("careers_apply_url") or job.get("url"),
                "description": clean_text(job.get("description", "")),
            })
        return items

    def save_item(self, item: dict) -> str:
        return upsert_job(self.db, item)

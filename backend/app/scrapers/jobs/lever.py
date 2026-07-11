from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.job_service import upsert_job
from app.services.cleaner import clean_text
from app.services.job_search import infer_employment_type, normalize_remote_type


class LeverScraper(BaseScraper):
    module = "jobs"

    def __init__(self, db: Session, company: str, company_slug: str):
        super().__init__(db)
        self.company = company
        self.company_slug = company_slug
        self.source_name = f"lever:{company_slug}"

    def fetch(self) -> list[dict]:
        url = f"https://api.lever.co/v0/postings/{self.company_slug}?mode=json"
        postings = self.fetch_url(url).json()
        items = []
        for job in postings:
            location = job.get("categories", {}).get("location")
            commitment = job.get("categories", {}).get("commitment")
            title = job.get("text")
            items.append({
                "title": title,
                "company": self.company,
                "location": location,
                "remote_type": normalize_remote_type(location),
                "employment_type": infer_employment_type(title, commitment),
                "source_name": self.source_name,
                "source_url": job.get("hostedUrl"),
                "apply_url": job.get("applyUrl") or job.get("hostedUrl"),
                "date_posted": None,
                "description": clean_text(job.get("descriptionPlain") or job.get("description")),
            })
        return items

    def save_item(self, item: dict) -> str:
        return upsert_job(self.db, item)

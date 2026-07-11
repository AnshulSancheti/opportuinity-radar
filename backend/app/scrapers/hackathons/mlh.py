import re

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.hackathon_service import upsert_hackathon
from app.services.date_parser import parse_date


def infer_hackathon_mode(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ("online", "digital", "virtual")):
        return "online"
    if "hybrid" in t:
        return "hybrid"
    return "offline"


class MLHScraper(BaseScraper):
    source_name = "mlh"
    module = "hackathons"

    EVENTS_URL = "https://mlh.io/events"

    def fetch(self) -> list[dict]:
        response = self.fetch_url(self.EVENTS_URL)
        soup = BeautifulSoup(response.text, "lxml")
        items = []
        for card in soup.select("[class*='event'], .event-card, article"):
            link = card.find("a", href=True)
            if not link:
                continue
            name = link.get_text(strip=True) or card.get_text(strip=True)[:100]
            if not name or len(name) < 3:
                continue
            href = link["href"]
            url = href if href.startswith("http") else f"https://mlh.io{href}"
            date_text = card.get_text(" ", strip=True)
            start_date = None
            date_match = re.search(r"([A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4})", date_text)
            if date_match:
                start_date = parse_date(date_match.group(1))
            location = None
            loc_match = re.search(r"([A-Z][a-z]+(?:,\s*[A-Z]{2})?(?:,\s*[A-Za-z ]+)?)", date_text)
            if loc_match and len(loc_match.group(1)) < 60:
                location = loc_match.group(1)
            items.append({
                "name": name,
                "organizer": "MLH",
                "url": url,
                "source_name": self.source_name,
                "mode": infer_hackathon_mode(date_text),
                "location": location,
                "start_date": start_date,
                "description": date_text[:500],
            })
        return items[:20]

    def save_item(self, item: dict) -> str:
        return upsert_hackathon(self.db, item)

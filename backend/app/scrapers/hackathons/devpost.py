"""Ingest Devpost's public open/upcoming hackathon listing, with bounded paging."""
import math
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from dateutil import parser
from app.scrapers.base import BaseScraper
from app.services.hackathon_service import upsert_hackathon


def submission_dates(value: str):
    # Source supplies calendar dates, not exact times/time zones. Use UTC day
    # boundaries for date filtering and display them as submission dates.
    parts = re.split(r"\s+(?:-|–|—)\s+", value.strip())
    if len(parts) == 1 and re.fullmatch(r"[A-Za-z]+ \d{1,2}, \d{4}", value.strip()):
        end = parser.parse(value).replace(tzinfo=timezone.utc, hour=23, minute=59, second=59, microsecond=999999)
        return None, end
    if len(parts) != 2 or not re.search(r"\b\d{4}\b", parts[1]):
        raise ValueError(f"Unrecognized Devpost submission period: {value}")
    if not re.search(r"[A-Za-z]", parts[1]):
        month = re.match(r"([A-Za-z]+)", parts[0])
        if not month:
            raise ValueError("Devpost submission month missing")
        parts[1] = month.group(1) + " " + parts[1]
    end = parser.parse(parts[1], default=datetime(2000, 1, 1)).replace(tzinfo=timezone.utc, hour=23, minute=59, second=59, microsecond=999999)
    start = parser.parse(parts[0], default=datetime(end.year, 1, 1)).replace(tzinfo=timezone.utc, hour=0, minute=0, second=0, microsecond=0)
    if start > end and not re.search(r"\b\d{4}\b", parts[0]):
        start = start.replace(year=start.year - 1)
    if start > end:
        raise ValueError("Devpost submission dates are reversed")
    return start, end


def parse_devpost_event(event: dict) -> dict:
    if not event.get("id") or not event.get("title") or not event.get("url", "").startswith("https://"):
        raise ValueError("Devpost event identity or URL missing")
    start, end = submission_dates(event.get("submission_period_dates", ""))
    location = (event.get("displayed_location") or {}).get("location")
    mode = "online" if location and location.lower() == "online" else "offline" if location else None
    return {
        "source_event_id": str(event["id"]), "source_name": "devpost", "name": event["title"],
        "url": event["url"], "organizer": event.get("organization_name"),
        "mode": mode, "location": location, "start_date": start, "end_date": end,
        "prize_text": BeautifulSoup(event.get("prize_amount") or "", "lxml").get_text("", strip=True) or None,
        "themes": [theme["name"] for theme in event.get("themes", []) if theme.get("name")],
        "application_status": event.get("open_state"),
        # Submission end is NOT a registration deadline; do not populate it.
    }


class DevpostScraper(BaseScraper):
    source_name = "devpost"
    module = "hackathons"
    max_pages = 30
    LISTING_URL = "https://devpost.com/api/hackathons?page={page}&status[]=open&status[]=upcoming"

    def fetch(self):
        items = []
        seen = set()
        pages = 1
        for page in range(1, self.max_pages + 1):
            data = self.fetch_url(self.LISTING_URL.format(page=page)).json()
            events, meta = data.get("hackathons"), data.get("meta", {})
            if not isinstance(events, list) or not isinstance(meta.get("total_count"), int) or not meta.get("per_page"):
                raise ValueError("Devpost listing structure changed")
            pages = math.ceil(meta["total_count"] / meta["per_page"])
            if pages > self.max_pages:
                raise ValueError("Devpost listing exceeds configured page limit; preserving previous data")
            if not events:
                raise ValueError("Devpost returned an unexpectedly empty listing page")
            for event in events:
                if event.get("open_state") not in {"open", "upcoming"}:
                    continue
                item = parse_devpost_event(event)
                if item["source_event_id"] not in seen:
                    items.append(item); seen.add(item["source_event_id"])
            if page >= pages:
                return items
        raise ValueError("Devpost pagination incomplete")

    def save_item(self, item):
        return upsert_hackathon(self.db, item)

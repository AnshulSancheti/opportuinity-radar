"""Read MLH's published event JSON; never infer fields from unrelated card text."""
import json
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper
from app.services.hackathon_service import upsert_hackathon
from app.services.date_parser import parse_date


def parse_mlh_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    script = soup.select_one('script[data-page="app"][type="application/json"]')
    if script is None:
        raise ValueError("MLH event data not found; source layout may have changed")
    data = json.loads(script.string or script.get_text())
    events = data.get("props", {}).get("upcomingEvents")
    if not isinstance(events, list) or not events:
        raise ValueError("MLH returned no structured upcoming events")
    items = []
    for event in events:
        start, end = parse_date(event.get("startsAt")), parse_date(event.get("endsAt"))
        url = event.get("websiteUrl")
        if not event.get("id") or not event.get("name") or not start or not end or not url or not url.startswith(("https://", "http://")):
            raise ValueError("MLH event is missing its identity, dates, or website")
        venue = event.get("venueAddress") or {}
        location = ", ".join(dict.fromkeys(v for v in (venue.get("city"), venue.get("state"), venue.get("country")) if v)) or event.get("location")
        items.append({
            "source_event_id": str(event["id"]), "name": event["name"],
            "url": url, "source_name": "mlh", "start_date": start, "end_date": end,
            "mode": {"physical": "offline", "digital": "online", "virtual": "online", "online": "online", "hybrid": "hybrid"}.get(event.get("formatType")),
            "location": location, "themes": [],
        })
    return items


class MLHScraper(BaseScraper):
    source_name = "mlh"
    module = "hackathons"
    EVENTS_URL = "https://mlh.io/events"

    def fetch(self):
        return parse_mlh_page(self.fetch_url(self.EVENTS_URL).text)

    def save_item(self, item):
        return upsert_hackathon(self.db, item)

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.hackathon_service import upsert_hackathon


# Expanded curated events — global + India-focused
STATIC_EVENTS = [
    {
        "name": "HackMIT 2026",
        "organizer": "MIT",
        "url": "https://hackmit.org",
        "mode": "offline",
        "location": "Cambridge, MA, USA",
        "start_date": datetime(2026, 9, 19, tzinfo=timezone.utc),
        "end_date": datetime(2026, 9, 21, tzinfo=timezone.utc),
        "prize_text": "Multiple tracks",
        "description": "Annual hackathon at MIT",
    },
    {
        "name": "ETHIndia 2026",
        "organizer": "ETHGlobal",
        "url": "https://ethindia.co",
        "mode": "offline",
        "location": "Bengaluru, India",
        "start_date": datetime(2026, 11, 28, tzinfo=timezone.utc),
        "end_date": datetime(2026, 11, 30, tzinfo=timezone.utc),
        "prize_text": "$100k+ prize pool",
        "description": "India's largest Ethereum hackathon",
    },
    {
        "name": "Smart India Hackathon 2026",
        "organizer": "Government of India",
        "url": "https://sih.gov.in",
        "mode": "hybrid",
        "location": "India",
        "start_date": datetime(2026, 8, 1, tzinfo=timezone.utc),
        "prize_text": "National level",
        "description": "World's biggest open innovation model",
    },
    {
        "name": "Hack the North 2026",
        "organizer": "University of Waterloo",
        "url": "https://hackthenorth.com",
        "mode": "hybrid",
        "location": "Waterloo, Canada",
        "start_date": datetime(2026, 9, 12, tzinfo=timezone.utc),
        "end_date": datetime(2026, 9, 14, tzinfo=timezone.utc),
        "description": "Canada's biggest hackathon",
    },
    {
        "name": "HackGT 2026",
        "organizer": "Georgia Tech",
        "url": "https://hack.gt",
        "mode": "offline",
        "location": "Atlanta, GA, USA",
        "start_date": datetime(2026, 10, 3, tzinfo=timezone.utc),
        "end_date": datetime(2026, 10, 5, tzinfo=timezone.utc),
        "description": "Georgia Tech's flagship hackathon",
    },
    {
        "name": "HackNYU 2026",
        "organizer": "NYU",
        "url": "https://hacknyu.org",
        "mode": "offline",
        "location": "New York, NY, USA",
        "start_date": datetime(2026, 2, 14, tzinfo=timezone.utc),
        "end_date": datetime(2026, 2, 16, tzinfo=timezone.utc),
        "description": "NYU annual hackathon",
    },
    {
        "name": "InOut 2026",
        "organizer": "Devfolio",
        "url": "https://inout.io",
        "mode": "online",
        "location": "India",
        "start_date": datetime(2026, 10, 10, tzinfo=timezone.utc),
        "end_date": datetime(2026, 10, 12, tzinfo=timezone.utc),
        "prize_text": "₹ prizes + swag",
        "description": "India's popular online hackathon by Devfolio",
    },
    {
        "name": "HackCBS 2026",
        "organizer": "Columbia Business School",
        "url": "https://hackcbs.tech",
        "mode": "offline",
        "location": "New Delhi, India",
        "start_date": datetime(2026, 11, 7, tzinfo=timezone.utc),
        "end_date": datetime(2026, 11, 9, tzinfo=timezone.utc),
        "description": "Major Delhi NCR hackathon",
    },
    {
        "name": "HackRice 2026",
        "organizer": "Rice University",
        "url": "https://hack.rice.edu",
        "mode": "offline",
        "location": "Houston, TX, USA",
        "start_date": datetime(2026, 9, 26, tzinfo=timezone.utc),
        "end_date": datetime(2026, 9, 28, tzinfo=timezone.utc),
        "description": "Rice University's annual hackathon",
    },
    {
        "name": "Hack the Valley 2026",
        "organizer": "University of Toronto",
        "url": "https://hackthevalley.io",
        "mode": "offline",
        "location": "Toronto, Canada",
        "start_date": datetime(2026, 10, 17, tzinfo=timezone.utc),
        "end_date": datetime(2026, 10, 19, tzinfo=timezone.utc),
        "description": "UTM's flagship hackathon",
    },
    {
        "name": "Junction 2026",
        "organizer": "Junction",
        "url": "https://hackjunction.com",
        "mode": "hybrid",
        "location": "Helsinki, Finland",
        "start_date": datetime(2026, 11, 14, tzinfo=timezone.utc),
        "end_date": datetime(2026, 11, 16, tzinfo=timezone.utc),
        "description": "Europe's leading hackathon",
    },
    {
        "name": "CodeDay 2026",
        "organizer": "CodeDay",
        "url": "https://codeday.org",
        "mode": "online",
        "location": "Global",
        "start_date": datetime(2026, 5, 17, tzinfo=timezone.utc),
        "end_date": datetime(2026, 5, 18, tzinfo=timezone.utc),
        "description": "Beginner-friendly 24-hour hackathon",
    },
    {
        "name": "Hack2Hire 2026",
        "organizer": "Various",
        "url": "https://devpost.com",
        "mode": "online",
        "location": "Global",
        "start_date": datetime(2026, 7, 12, tzinfo=timezone.utc),
        "end_date": datetime(2026, 7, 14, tzinfo=timezone.utc),
        "description": "Career-focused virtual hackathon",
    },
    {
        "name": "HackHarvard 2026",
        "organizer": "Harvard University",
        "url": "https://hackharvard.io",
        "mode": "offline",
        "location": "Cambridge, MA, USA",
        "start_date": datetime(2026, 10, 24, tzinfo=timezone.utc),
        "end_date": datetime(2026, 10, 26, tzinfo=timezone.utc),
        "description": "Harvard's annual hackathon",
    },
    {
        "name": "HackIllinois 2026",
        "organizer": "University of Illinois",
        "url": "https://hackillinois.org",
        "mode": "offline",
        "location": "Urbana-Champaign, IL, USA",
        "start_date": datetime(2026, 2, 28, tzinfo=timezone.utc),
        "end_date": datetime(2026, 3, 2, tzinfo=timezone.utc),
        "description": "UIUC's premier hackathon",
    },
    {
        "name": "HackSociety 2026",
        "organizer": "HackSociety",
        "url": "https://hacksociety.tech",
        "mode": "online",
        "location": "India",
        "start_date": datetime(2026, 8, 22, tzinfo=timezone.utc),
        "end_date": datetime(2026, 8, 24, tzinfo=timezone.utc),
        "description": "India-focused online hackathon",
    },
    {
        "name": "HackTheMountains 2026",
        "organizer": "Appalachian State",
        "url": "https://hackthemountains.dev",
        "mode": "offline",
        "location": "Boone, NC, USA",
        "start_date": datetime(2026, 4, 11, tzinfo=timezone.utc),
        "end_date": datetime(2026, 4, 13, tzinfo=timezone.utc),
        "description": "Regional US hackathon",
    },
]


class StaticListScraper(BaseScraper):
    source_name = "static_list"
    module = "hackathons"

    def fetch(self) -> list[dict]:
        return [{**event, "source_name": self.source_name} for event in STATIC_EVENTS]

    def save_item(self, item: dict) -> str:
        return upsert_hackathon(self.db, item)

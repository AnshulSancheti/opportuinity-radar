from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.scrapers.base import BaseScraper
from app.services.article_service import upsert_article


HN_API = "https://hacker-news.firebaseio.com/v0"


class HackerNewsScraper(BaseScraper):
    source_name = "hacker_news"
    module = "news"

    def fetch(self) -> list[dict]:
        top_ids = self.fetch_url(f"{HN_API}/topstories.json").json()[:30]
        items = []
        for story_id in top_ids:
            story = self.fetch_url(f"{HN_API}/item/{story_id}.json").json()
            if story.get("type") != "story":
                continue
            url = story.get("url")
            if not url:
                url = f"https://news.ycombinator.com/item?id={story_id}"
            published = datetime.fromtimestamp(story.get("time", 0), tz=timezone.utc)
            items.append({
                "title": story.get("title", ""),
                "url": url,
                "source_name": "Hacker News",
                "author": story.get("by"),
                "published_at": published,
                "score": story.get("score"),
                "summary": None,
            })
        return items

    def save_item(self, item: dict) -> str:
        return upsert_article(self.db, item)

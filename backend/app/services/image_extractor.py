"""Extract image URLs from RSS entries and HTML snippets."""

from __future__ import annotations

import re
from html import unescape
from urllib.parse import urlparse

_IMG_SRC_RE = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.IGNORECASE)


def is_valid_image_url(url: str | None) -> bool:
    if not url or not url.strip():
        return False
    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def first_img_from_html(html: str | None) -> str | None:
    if not html:
        return None
    match = _IMG_SRC_RE.search(unescape(html))
    if match and is_valid_image_url(match.group(1)):
        return match.group(1).strip()
    return None


def extract_rss_image(entry) -> str | None:
    """Best-effort image URL from a feedparser entry."""
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        thumb = entry.media_thumbnail[0]
        url = thumb.get("url") if isinstance(thumb, dict) else getattr(thumb, "url", None)
        if is_valid_image_url(url):
            return url

    if hasattr(entry, "media_content") and entry.media_content:
        for media in entry.media_content:
            url = media.get("url") if isinstance(media, dict) else getattr(media, "url", None)
            medium = media.get("medium") if isinstance(media, dict) else getattr(media, "medium", None)
            mtype = media.get("type") if isinstance(media, dict) else getattr(media, "type", "")
            if url and (medium == "image" or str(mtype).startswith("image/")):
                if is_valid_image_url(url):
                    return url

    for link in getattr(entry, "links", []) or []:
        if link.get("type", "").startswith("image/") and is_valid_image_url(link.get("href")):
            return link["href"]

    for field in ("summary", "description", "content"):
        value = entry.get(field) if hasattr(entry, "get") else getattr(entry, field, None)
        if isinstance(value, list) and value:
            value = value[0].get("value", "")
        img = first_img_from_html(str(value) if value else None)
        if img:
            return img

    return None

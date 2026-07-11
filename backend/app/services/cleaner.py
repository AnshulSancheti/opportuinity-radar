import hashlib
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid", "gclid"}


def clean_text(text: str | None) -> str | None:
    if not text:
        return None
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def normalize_whitespace(text: str | None) -> str | None:
    if not text:
        return None
    return re.sub(r"\s+", " ", text).strip()


def normalize_name(text: str | None) -> str | None:
    if not text:
        return None
    return normalize_whitespace(text).lower()


def remove_tracking_params(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in query.items() if k.lower() not in TRACKING_PARAMS}
    new_query = urlencode(filtered, doseq=True)
    return urlunparse(parsed._replace(query=new_query, fragment=""))


def canonicalize_url(url: str | None) -> str | None:
    if not url:
        return None
    url = remove_tracking_params(url.strip())
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or ""
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def make_content_hash(*parts: str | None) -> str:
    normalized = "|".join((normalize_name(p) or "" for p in parts))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

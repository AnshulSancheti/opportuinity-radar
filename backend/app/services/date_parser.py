from datetime import datetime, timedelta, timezone

from dateutil import parser as date_parser


def parse_date(value: str | None, reference: datetime | None = None) -> datetime | None:
    if not value:
        return None
    text = value.strip().lower()
    ref = reference or datetime.now(timezone.utc)

    relative_patterns = [
        (r"tomorrow", 1),
        (r"in (\d+) days?", None),
        (r"ends? in (\d+) days?", None),
    ]
    for pattern, fixed_days in relative_patterns:
        import re

        match = re.search(pattern, text)
        if match:
            days = fixed_days if fixed_days is not None else int(match.group(1))
            return ref + timedelta(days=days)

    try:
        parsed = date_parser.parse(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (ValueError, TypeError, OverflowError):
        return None

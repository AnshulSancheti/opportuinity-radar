"""Job search helpers: remote/employment normalization and text query building."""

from __future__ import annotations

import re

from sqlalchemy import ColumnElement, func, or_

from app.models import Job

INTERN_PATTERN = re.compile(r"\b(internship|intern|co-?op)\b", re.IGNORECASE)


def normalize_remote_type(
    location: str | None,
    is_remote_flag: bool | None = None,
) -> str:
    """Return remote | hybrid | onsite from location text and optional API flag."""
    loc = (location or "").lower()
    if is_remote_flag is True and not loc:
        return "remote"
    if any(k in loc for k in ("hybrid", "flexible")):
        return "hybrid"
    if any(k in loc for k in ("remote", "wfh", "work from home", "distributed", "anywhere")):
        return "remote"
    if is_remote_flag is True:
        return "remote"
    if location and location.strip():
        return "onsite"
    return "onsite"


def infer_employment_type(title: str | None, commitment: str | None = None) -> str | None:
    """Infer employment type from title and optional ATS commitment field."""
    if commitment and commitment.strip():
        c = commitment.strip()
        if INTERN_PATTERN.search(c):
            return "Internship"
        return c

    t = (title or "").lower()
    if INTERN_PATTERN.search(t):
        return "Internship"
    if "part-time" in t or "part time" in t:
        return "Part-time"
    if "contract" in t and "contractor" not in t:
        return "Contract"
    if "full-time" in t or "full time" in t:
        return "Full-time"
    return None


def _ilike(column, term: str) -> ColumnElement[bool]:
    return column.ilike(f"%{term}%")


def build_job_text_conditions(q: str) -> list[ColumnElement[bool]]:
    """Build OR conditions for free-text job search."""
    term = q.strip()
    if not term:
        return []

    conditions: list[ColumnElement[bool]] = [
        _ilike(Job.title, term),
        _ilike(Job.company, term),
        _ilike(Job.description, term),
        _ilike(Job.summary, term),
        _ilike(Job.employment_type, term),
        _ilike(Job.location, term),
        func.array_to_string(Job.skills, " ").ilike(f"%{term}%"),
    ]

    if INTERN_PATTERN.search(term):
        for pattern in ("intern", "internship", "co-op", "coop"):
            conditions.append(_ilike(Job.title, pattern))
            conditions.append(_ilike(Job.employment_type, pattern))

    return conditions


def apply_remote_type_filter(query, remote_type: str):
    """Apply remote_type filter with onsite fallback for legacy null rows."""
    if remote_type == "onsite":
        return query.where(
            or_(
                Job.remote_type == "onsite",
                Job.remote_type.is_(None),
            )
        )
    return query.where(Job.remote_type == remote_type)

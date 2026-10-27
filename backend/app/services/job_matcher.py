"""Job matching agent.

Scores scraped jobs against a candidate resume using the Anthropic API and
persists one verdict per (job, profile) pair.

The resume is the stable prefix of every request and the job posting is the
varying suffix, so the resume carries a `cache_control` breakpoint. Note that
caching only activates once the cached prefix clears the model's minimum:
4096 tokens on claude-haiku-4-5, 512 on claude-opus-5. A one-page resume sits
below the Haiku minimum, so expect `cache_read_input_tokens` to stay at 0
there — the breakpoint costs nothing and starts paying off on a larger model
or a longer profile.
"""

from __future__ import annotations

import logging

import anthropic
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import CandidateProfile, Job, JobMatch
from app.schemas import MatchAssessment

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You assess the distance between one candidate and one job, \
so they know both where they stand today and what would close the gap.

Judge only on evidence. If the profile does not show a skill, it is missing — \
do not credit adjacent or assumed experience, and do not treat interest in a \
field as experience in it. Weigh requirements the posting treats as mandatory \
above its wish list.

Score present-day readiness, not potential. Seniority gaps are real gaps: a \
staff role is not a 70 for a student because the languages overlap. Most \
roles a student looks at should score low, and that is useful information, \
not a failure.

Then give the closing move. This is the part the candidate acts on, so it \
must be specific enough to start this week — name the system to build or the \
concept to learn, not a category. "Ship a service that handles auth and \
rate limiting under load" is a closing move. "Improve backend skills" is \
not. If a single missing item is doing most of the blocking, say that one \
thing rather than listing everything.

Be blunt in both directions. An inflated score wastes an application the \
candidate cannot get back; a vague closing move wastes a month."""

# USD per million tokens (input, output).
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
}


class MatchingDisabled(RuntimeError):
    """Raised when the feature is called without an API key configured."""


def _max_tokens(model: str) -> int:
    """Haiku 4.5 does not think, so a small cap is safe. Newer models run
    adaptive thinking by default and `max_tokens` caps thinking plus response
    text together, so they need room or the JSON truncates mid-object."""
    return 2048 if model.startswith("claude-haiku") else 16000


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = PRICING.get(model)
    if not rates:
        return 0.0
    in_rate, out_rate = rates
    return round(input_tokens / 1_000_000 * in_rate + output_tokens / 1_000_000 * out_rate, 6)


def active_profile(db: Session) -> CandidateProfile | None:
    return db.scalar(
        select(CandidateProfile).where(CandidateProfile.is_active).order_by(CandidateProfile.id.desc())
    )


def _job_brief(job: Job) -> str:
    """Render a job as text for the model. Descriptions are truncated because
    postings routinely carry kilobytes of boilerplate benefits copy that adds
    tokens without adding signal."""
    parts = [
        f"Title: {job.title}",
        f"Company: {job.company}",
    ]
    if job.location:
        parts.append(f"Location: {job.location}")
    if job.remote_type:
        parts.append(f"Remote: {job.remote_type}")
    if job.employment_type:
        parts.append(f"Employment type: {job.employment_type}")
    if job.experience_level:
        parts.append(f"Experience level: {job.experience_level}")
    if job.salary_text:
        parts.append(f"Compensation: {job.salary_text}")
    if job.skills:
        parts.append(f"Listed skills: {', '.join(job.skills)}")
    if job.description:
        description = job.description[:4000]
        parts.append(f"Description:\n{description}")
    return "\n".join(parts)


def _client() -> anthropic.Anthropic:
    settings = get_settings()
    if not settings.matching_enabled:
        raise MatchingDisabled("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def score_job(
    client: anthropic.Anthropic,
    model: str,
    profile: CandidateProfile,
    job: Job,
) -> tuple[MatchAssessment, int, int]:
    """Score one job. Returns the assessment plus token usage."""
    profile_block = f"CANDIDATE RESUME\n{profile.resume_text}"
    if profile.preferences:
        profile_block += f"\n\nSTATED PREFERENCES\n{profile.preferences}"

    response = client.messages.parse(
        model=model,
        max_tokens=_max_tokens(model),
        system=[
            {"type": "text", "text": SYSTEM_PROMPT},
            {
                "type": "text",
                "text": profile_block,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[{"role": "user", "content": f"JOB POSTING\n{_job_brief(job)}"}],
        output_format=MatchAssessment,
    )

    if response.stop_reason == "refusal":
        raise RuntimeError(f"model declined to score job {job.id}")

    assessment = response.parsed_output
    if assessment is None:
        raise RuntimeError(f"model returned unparseable output for job {job.id}")

    return assessment, response.usage.input_tokens, response.usage.output_tokens


def _upsert_match(
    db: Session,
    job: Job,
    profile: CandidateProfile,
    assessment: MatchAssessment,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    existing = db.scalar(
        select(JobMatch).where(JobMatch.job_id == job.id, JobMatch.profile_id == profile.id)
    )
    target = existing or JobMatch(job_id=job.id, profile_id=profile.id)
    target.score = assessment.score
    target.verdict = assessment.verdict
    target.reasoning = assessment.reasoning
    target.matched_skills = assessment.matched_skills
    target.missing_skills = assessment.missing_skills
    target.closing_move = assessment.closing_move
    target.model = model
    target.input_tokens = input_tokens
    target.output_tokens = output_tokens
    if existing is None:
        db.add(target)


def run_matching(db: Session, limit: int, rescore: bool = False) -> dict:
    """Score up to `limit` active jobs against the active profile.

    A per-job failure is logged and counted rather than aborting the batch —
    one bad posting should not discard the verdicts already earned.
    """
    settings = get_settings()
    client = _client()
    model = settings.match_model

    profile = active_profile(db)
    if profile is None:
        raise LookupError("no active candidate profile — POST a resume first")

    query = select(Job).where(Job.status == "active")
    if not rescore:
        scored_ids = select(JobMatch.job_id).where(JobMatch.profile_id == profile.id)
        query = query.where(Job.id.not_in(scored_ids))
    jobs = db.scalars(
        query.order_by(Job.date_posted.desc().nullslast(), Job.first_seen_at.desc()).limit(limit)
    ).all()

    scored = failed = 0
    total_in = total_out = 0

    for job in jobs:
        try:
            assessment, tokens_in, tokens_out = score_job(client, model, profile, job)
        except anthropic.RateLimitError:
            logger.warning("rate limited while scoring job %s — stopping batch early", job.id)
            break
        except (anthropic.APIStatusError, anthropic.APIConnectionError, RuntimeError) as exc:
            logger.warning("failed to score job %s: %s", job.id, exc)
            failed += 1
            continue

        _upsert_match(db, job, profile, assessment, model, tokens_in, tokens_out)
        scored += 1
        total_in += tokens_in
        total_out += tokens_out

    db.commit()

    return {
        "scored": scored,
        "skipped": len(jobs) - scored - failed,
        "failed": failed,
        "model": model,
        "input_tokens": total_in,
        "output_tokens": total_out,
        "estimated_cost_usd": estimate_cost(model, total_in, total_out),
    }

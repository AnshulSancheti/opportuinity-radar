import pytest
from pydantic import ValidationError

from app.models import Job
from app.schemas import MatchAssessment
from app.services.job_matcher import _job_brief, _max_tokens, estimate_cost


def make_job(**overrides) -> Job:
    defaults = dict(
        id=1,
        title="Backend Engineer",
        company="Acme",
        location="Bengaluru, India",
        remote_type="hybrid",
        employment_type="Full-time",
        experience_level=None,
        salary_text=None,
        skills=["Python", "PostgreSQL"],
        description="Build APIs with FastAPI.",
    )
    defaults.update(overrides)
    return Job(**defaults)


def test_job_brief_includes_core_fields():
    brief = _job_brief(make_job())
    assert "Title: Backend Engineer" in brief
    assert "Company: Acme" in brief
    assert "Python, PostgreSQL" in brief
    assert "FastAPI" in brief


def test_job_brief_omits_absent_fields():
    brief = _job_brief(make_job(location=None, salary_text=None, skills=[]))
    assert "Location:" not in brief
    assert "Compensation:" not in brief
    assert "Listed skills:" not in brief


def test_job_brief_truncates_long_descriptions():
    brief = _job_brief(make_job(description="x" * 10_000))
    assert len(brief) < 5_000


def test_max_tokens_leaves_room_for_thinking_on_newer_models():
    # Haiku 4.5 never thinks, so a tight cap is safe. Newer models run adaptive
    # thinking by default and max_tokens caps thinking + text together, so a
    # tight cap there would truncate the JSON mid-object.
    assert _max_tokens("claude-haiku-4-5") == 2048
    assert _max_tokens("claude-opus-5") == 16000
    assert _max_tokens("claude-sonnet-5") == 16000


def test_estimate_cost_known_model():
    # 1M input + 1M output on Haiku 4.5 at $1/$5.
    assert estimate_cost("claude-haiku-4-5", 1_000_000, 1_000_000) == pytest.approx(6.0)


def test_estimate_cost_unknown_model_is_zero_not_a_crash():
    assert estimate_cost("some-future-model", 1000, 1000) == 0.0


def test_assessment_rejects_out_of_range_score():
    with pytest.raises(ValidationError):
        MatchAssessment(
            score=140,
            verdict="strong",
            reasoning="...",
            matched_skills=[],
            missing_skills=[],
        )


def test_assessment_rejects_unknown_verdict():
    with pytest.raises(ValidationError):
        MatchAssessment(
            score=50,
            verdict="excellent",
            reasoning="...",
            matched_skills=[],
            missing_skills=[],
        )


def test_assessment_accepts_valid_payload():
    assessment = MatchAssessment(
        score=82,
        verdict="strong",
        reasoning="Resume shows FastAPI and Postgres, which the posting requires.",
        matched_skills=["Python", "PostgreSQL"],
        missing_skills=["Kubernetes"],
        closing_move="Build a small Kubernetes deployment for a FastAPI project.",
    )
    assert assessment.score == 82
    assert assessment.verdict == "strong"

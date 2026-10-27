import pytest

from app.services.cleaner import canonicalize_url, make_content_hash, remove_tracking_params
from app.services.categorizer import categorize
from app.services.skill_extractor import extract_skills
from app.services.date_parser import parse_date
from app.services.job_search import (
    build_job_text_conditions,
    infer_employment_type,
    infer_experience_level,
    normalize_remote_type,
)


def test_remove_tracking_params():
    url = "https://example.com/job?utm_source=twitter&id=1"
    assert "utm_source" not in remove_tracking_params(url)
    assert "id=1" in remove_tracking_params(url)


def test_content_hash_stable():
    h1 = make_content_hash("Python Dev", "Acme", "greenhouse")
    h2 = make_content_hash("python dev", "acme", "greenhouse")
    assert h1 == h2


def test_categorize_ai():
    assert categorize("OpenAI releases new LLM model") == "AI/ML"


def test_extract_skills():
    skills = extract_skills("We need Python, SQL, and Docker experience")
    assert "Python" in skills
    assert "SQL" in skills


def test_parse_date():
    result = parse_date("2026-07-20")
    assert result is not None
    assert result.year == 2026


def test_infer_employment_type_intern_from_title():
    assert infer_employment_type("Software Engineer Intern") == "Internship"
    assert infer_employment_type("Summer Co-op Developer") == "Internship"


def test_infer_employment_type_from_commitment():
    assert infer_employment_type("Engineer", "Internship") == "Internship"
    assert infer_employment_type("Engineer", "Full-time") == "Full-time"


def test_normalize_remote_type():
    assert normalize_remote_type("Remote - US") == "remote"
    assert normalize_remote_type("Hybrid - San Francisco") == "hybrid"
    assert normalize_remote_type("Bengaluru, India") == "onsite"
    assert normalize_remote_type(None, is_remote_flag=True) == "remote"


def test_build_job_text_conditions_intern_expansion():
    conditions = build_job_text_conditions("internship")
    assert len(conditions) >= 7


def test_infer_experience_level_ladder():
    assert infer_experience_level("Software Engineer Intern") == "internship"
    assert infer_experience_level("Junior Backend Developer") == "junior"
    assert infer_experience_level("Software Engineer II") == "mid"
    assert infer_experience_level("Senior Software Engineer") == "senior"
    assert infer_experience_level("Staff Software Engineer") == "staff"
    assert infer_experience_level("Principal Engineer") == "principal"
    assert infer_experience_level("Director of Engineering") == "executive"


def test_infer_experience_level_prefers_more_senior_marker():
    # "Senior Staff" is a staff-level role, not a senior-level one.
    assert infer_experience_level("Senior Staff Software Engineer") == "staff"


def test_infer_experience_level_unknown_is_none():
    # An unmarked title is genuinely unknown; guessing "mid" would be a lie the
    # matching agent then reasons from.
    assert infer_experience_level("Software Engineer") is None
    assert infer_experience_level("Backend Developer") is None
    assert infer_experience_level(None) is None


def test_infer_experience_level_does_not_match_intern_inside_internal():
    assert infer_experience_level("Senior Internal Tools Engineer") == "senior"


def test_infer_experience_level_ai_is_not_level_one():
    # "AI" must not trip the standalone-"I" junior marker.
    assert infer_experience_level("AI Engineer") is None

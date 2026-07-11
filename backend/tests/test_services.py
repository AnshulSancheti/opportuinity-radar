import pytest

from app.services.cleaner import canonicalize_url, make_content_hash, remove_tracking_params
from app.services.categorizer import categorize
from app.services.skill_extractor import extract_skills
from app.services.date_parser import parse_date
from app.services.job_search import infer_employment_type, normalize_remote_type, build_job_text_conditions


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

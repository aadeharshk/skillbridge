from pathlib import Path

from matcher.core import match, parse_requirements
from matcher.skills import extract_skills

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def test_java_is_not_javascript():
    assert extract_skills("Built apps in JavaScript") == {"JavaScript"}
    assert "Java" in extract_skills("Backend in Java and Spring")


def test_implied_skills_only_when_expanded():
    assert "Workflow Automation" not in extract_skills("Used n8n")
    assert "Workflow Automation" in extract_skills("Used n8n", expand=True)


def test_nice_to_have_section_is_optional():
    reqs = parse_requirements("Title\nRequirements\n- Strong SQL skills for analytics work\nNice to have\n- Experience with Apache Spark at scale")
    assert [r.optional for r in reqs] == [False, True]


def test_sample_resume_ranks_analyst_job_first():
    resume = (SAMPLES / "sample_resume.txt").read_text()
    scores = {p.stem: match(resume, p.read_text()).score for p in SAMPLES.glob("jd_*.txt")}
    assert max(scores, key=scores.get) == "jd_data_analyst"

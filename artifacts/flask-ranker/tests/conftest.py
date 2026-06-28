"""Pytest fixtures with mock candidate data."""

import pytest
from typing import Any


def _make_candidate(
    candidate_id: str,
    title: str,
    yoe: float,
    company: str,
    is_consulting: bool = False,
    skills: list[str] | None = None,
    has_production: bool = True,
    country: str = "India",
    open_to_work: bool = True,
) -> dict[str, Any]:
    """Build a minimal candidate dict for testing."""
    consulting_firms = ["TCS", "Infosys", "Wipro"]
    skill_objs = [{"name": s, "proficiency": "intermediate"} for s in (skills or [])]
    description = "Deployed ML pipeline to production. Served inference at low latency." if has_production else "Published paper on embeddings. Academic research lab."
    return {
        "candidate_id": candidate_id,
        "current_title": title,
        "headline": title,
        "years_of_experience": yoe,
        "country": country,
        "location": f"Bangalore, {country}",
        "willing_to_relocate": True,
        "skills": skill_objs,
        "summary": f"Senior engineer with {yoe} years building AI systems.",
        "career_history": [
            {
                "company": consulting_firms[0] if is_consulting else company,
                "title": title,
                "duration_months": int(yoe * 12),
                "description": description,
            }
        ],
        "redrob_signals": {
            "last_active_date": "2026-06-01",
            "open_to_work_flag": open_to_work,
            "notice_period_days": 30,
            "recruiter_response_rate": 0.8,
            "interview_completion_rate": 0.9,
            "github_activity_score": 75,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
            "profile_completeness_score": 90,
        },
    }


@pytest.fixture
def mock_candidates() -> list[dict[str, Any]]:
    """Five mock candidates covering various profile types."""
    return [
        _make_candidate(
            "c001", "Senior AI Engineer", 7.0, "Startup Inc",
            skills=["embeddings", "faiss", "python", "sentence-transformers", "vector database"],
        ),
        _make_candidate(
            "c002", "ML Engineer", 4.0, "Product Co",
            is_consulting=False,
            skills=["python", "pytorch", "nlp"],
        ),
        _make_candidate(
            "c003", "Data Scientist", 12.0, "TCS",
            is_consulting=True,
            skills=["python", "sql", "pandas"],
        ),
        _make_candidate(
            "c004", "Research Scientist", 6.0, "University Lab",
            has_production=False,
            skills=["embeddings", "faiss", "python"],
        ),
        _make_candidate(
            "c005", "Senior AI Engineer", 7.5, "Vector DB Corp",
            skills=["embeddings", "pinecone", "weaviate", "qdrant", "faiss",
                    "python", "sentence-transformers", "ranking", "ndcg"],
        ),
    ]


@pytest.fixture
def consulting_only_candidate() -> dict[str, Any]:
    """A candidate whose entire career is at consulting firms."""
    return _make_candidate(
        "c010", "ML Consultant", 8.0, "TCS",
        is_consulting=True,
        skills=["python", "machine learning"],
    )


@pytest.fixture
def honeypot_candidate() -> dict[str, Any]:
    """A candidate with implausible years of experience."""
    return {
        "candidate_id": "c020",
        "current_title": "AI Expert",
        "years_of_experience": 55,
        "country": "India",
        "skills": [],
        "career_history": [],
        "redrob_signals": {},
    }


@pytest.fixture
def hr_keyword_stuffer() -> dict[str, Any]:
    """An HR Manager with many AI keywords — keyword stuffer."""
    skills = [
        {"name": kw} for kw in [
            "AI", "ML", "machine learning", "deep learning", "neural", "GPT",
            "LLM", "NLP",
        ]
    ]
    return {
        "candidate_id": "c030",
        "current_title": "HR Manager",
        "years_of_experience": 5,
        "country": "India",
        "skills": skills,
        "career_history": [],
        "redrob_signals": {},
    }

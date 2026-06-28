"""Integration tests — full pipeline from candidates to valid CSV output."""

import csv
import io
import pytest
from src.parsers.candidate_parser import load_candidates
from src.ranker import hybrid_ranker, reasoning_generator


def _build_10_candidates():
    """Build 10 mock candidates with varied profiles for integration testing."""
    candidates = []
    for i in range(10):
        candidates.append({
            "candidate_id": f"int_{i:03d}",
            "current_title": "Senior AI Engineer" if i % 2 == 0 else "Data Scientist",
            "years_of_experience": 5 + i % 7,
            "country": "India",
            "willing_to_relocate": True,
            "skills": [
                {"name": "python"},
                {"name": "embeddings"} if i < 5 else {"name": "pandas"},
                {"name": "faiss"} if i < 3 else {"name": "sql"},
            ],
            "summary": f"Candidate {i} with ML experience.",
            "career_history": [
                {
                    "company": "Product Co" if i % 3 != 0 else "TCS",
                    "title": "Engineer",
                    "duration_months": 36 + i * 6,
                    "description": "Deployed models to production. Served inference." if i < 6 else "Academic research.",
                }
            ],
            "redrob_signals": {
                "last_active_date": "2026-05-15",
                "open_to_work_flag": i % 2 == 0,
                "notice_period_days": 30 + i * 10,
                "recruiter_response_rate": 0.7,
                "interview_completion_rate": 0.8,
                "github_activity_score": 50 + i * 5,
                "verified_email": True,
                "verified_phone": i % 2 == 0,
                "linkedin_connected": True,
                "profile_completeness_score": 75 + i,
            },
        })
    return candidates


def test_full_pipeline_10_candidates():
    """Full pipeline: 10 candidates → ranked list → valid CSV."""
    candidates = _build_10_candidates()
    loaded = load_candidates(candidates)
    assert len(loaded) == 10

    ranked = hybrid_ranker.rank(loaded)
    for r in ranked:
        r["reasoning"] = reasoning_generator.generate(r)

    # All 10 candidates are ranked
    assert len(ranked) == 10

    # Ranks are unique integers 1-10
    ranks = sorted(r["rank"] for r in ranked)
    assert ranks == list(range(1, 11))

    # Scores are non-increasing
    scores = [r["_final_score"] for r in ranked]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1] - 1e-9

    # candidate_ids are unique
    ids = [r["candidate_id"] for r in ranked]
    assert len(set(ids)) == 10

    # All scores in [0, 1]
    for r in ranked:
        assert 0.0 <= r["_final_score"] <= 1.0

    # Reasoning is a non-empty string
    for r in ranked:
        assert isinstance(r["reasoning"], str)
        assert len(r["reasoning"]) > 0

    # CSV output has correct format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])
    for r in ranked:
        writer.writerow([r["candidate_id"], r["rank"], round(r["_final_score"], 4), r["reasoning"]])
    csv_content = output.getvalue()

    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    assert len(rows) == 10
    for row in rows:
        assert "candidate_id" in row
        assert "rank" in row
        assert "score" in row
        assert "reasoning" in row
        assert float(row["score"]) >= 0.0
        assert int(row["rank"]) >= 1

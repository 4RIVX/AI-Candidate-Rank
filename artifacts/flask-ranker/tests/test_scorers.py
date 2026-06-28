"""Tests for individual scorer modules."""

import pytest
from src.scoring import experience_scorer, skill_scorer, behavioral_scorer


def test_experience_scorer_returns_float_0_1(mock_candidates):
    """Test that experience scorer returns float in [0.0, 1.0] for each candidate."""
    for c in mock_candidates:
        result = experience_scorer.score(c)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


def test_skill_scorer_returns_float_0_1(mock_candidates):
    """Test that skill scorer returns float in [0.0, 1.0] for each candidate."""
    for c in mock_candidates:
        result = skill_scorer.score(c)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


def test_behavioral_scorer_returns_float_0_1(mock_candidates):
    """Test that behavioral scorer returns float in [0.0, 1.0] for each candidate."""
    for c in mock_candidates:
        result = behavioral_scorer.score(c)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


def test_consulting_only_scores_low_on_experience(consulting_only_candidate):
    """A consulting-only candidate should score low on experience (company sub-score)."""
    result = experience_scorer.score(consulting_only_candidate)
    # Consulting only => company sub-score of 0.2 which drags final down
    assert result < 0.7


def test_vector_db_candidate_scores_high_on_skills():
    """A candidate with multiple vector DB skills should score high on skill scorer."""
    candidate = {
        "candidate_id": "c099",
        "skills": [
            {"name": "embeddings"},
            {"name": "faiss"},
            {"name": "pinecone"},
            {"name": "weaviate"},
            {"name": "python"},
            {"name": "sentence-transformers"},
            {"name": "ranking"},
            {"name": "ndcg"},
        ],
        "career_history": [],
    }
    result = skill_scorer.score(candidate)
    assert result >= 0.7


def test_experience_scorer_invalid_input():
    """Experience scorer should raise ValueError for non-dict input."""
    with pytest.raises(ValueError):
        experience_scorer.score("not a dict")


def test_skill_scorer_invalid_input():
    """Skill scorer should raise ValueError for non-dict input."""
    with pytest.raises(ValueError):
        skill_scorer.score(None)

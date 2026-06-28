"""Tests for the hybrid_ranker module."""

import pytest
from src.ranker.hybrid_ranker import rank


def test_output_sorted_descending_by_score(mock_candidates):
    """Ranked output should be sorted by final score descending."""
    results = rank(mock_candidates)
    scores = [r["_final_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_ranks_are_unique_integers(mock_candidates):
    """Ranks should be unique integers from 1 to N."""
    results = rank(mock_candidates)
    ranks = [r["rank"] for r in results]
    n = len(mock_candidates)
    assert sorted(ranks) == list(range(1, n + 1))


def test_no_duplicate_candidate_ids(mock_candidates):
    """No two results should share the same candidate_id."""
    results = rank(mock_candidates)
    ids = [r["candidate_id"] for r in results]
    assert len(ids) == len(set(ids))


def test_top_n_limits_output(mock_candidates):
    """top_n parameter should limit the returned list."""
    results = rank(mock_candidates, top_n=3)
    assert len(results) == 3


def test_empty_candidates_raises_error():
    """Passing an empty list should raise ValueError."""
    with pytest.raises(ValueError):
        rank([])


def test_scores_dict_present(mock_candidates):
    """Each result should have a 'scores' dict with all dimensions."""
    results = rank(mock_candidates)
    for r in results:
        assert "scores" in r
        scores = r["scores"]
        for key in ("semantic", "experience", "skill", "behavioral", "final", "disqualifier_multiplier"):
            assert key in scores

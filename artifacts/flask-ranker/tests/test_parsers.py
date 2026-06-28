"""Tests for candidate_parser module."""

import json
import pytest
from src.parsers.candidate_parser import parse_candidates, build_text_representation


def test_valid_json_array_loads():
    """Test that a valid JSON array is parsed into a list of dicts."""
    data = [{"candidate_id": "c001", "current_title": "Engineer"}]
    raw = json.dumps(data)
    result = parse_candidates(raw)
    assert len(result) == 1
    assert result[0]["candidate_id"] == "c001"


def test_valid_jsonl_loads():
    """Test that a valid JSONL string is parsed into a list of dicts."""
    lines = [
        json.dumps({"candidate_id": "c001", "current_title": "Engineer"}),
        json.dumps({"candidate_id": "c002", "current_title": "Scientist"}),
    ]
    raw = "\n".join(lines)
    result = parse_candidates(raw)
    assert len(result) == 2
    assert result[1]["candidate_id"] == "c002"


def test_missing_candidate_id_raises_error():
    """Test that a candidate missing candidate_id raises ValueError."""
    data = [{"current_title": "Engineer"}]
    raw = json.dumps(data)
    with pytest.raises(ValueError, match="candidate_id"):
        parse_candidates(raw)


def test_malformed_json_raises_error():
    """Test that malformed JSON raises ValueError."""
    with pytest.raises(ValueError, match="Failed to parse"):
        parse_candidates("{not valid json")


def test_build_text_representation_includes_skills():
    """Test that build_text_representation includes skill names."""
    candidate = {
        "candidate_id": "c001",
        "headline": "ML Engineer",
        "summary": "Builds models.",
        "skills": [{"name": "FAISS"}, {"name": "Python"}],
        "career_history": [{"description": "Deployed pipelines."}],
    }
    text = build_text_representation(candidate)
    assert "FAISS" in text
    assert "Python" in text
    assert "Deployed pipelines" in text

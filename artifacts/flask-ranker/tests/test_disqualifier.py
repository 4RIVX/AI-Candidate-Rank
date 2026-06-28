"""Tests for the disqualifier module."""

import pytest
from src.scoring.disqualifier import get_multiplier
from src.config import (
    HONEYPOT_MULTIPLIER,
    KEYWORD_STUFFER_MULTIPLIER,
    CONSULTING_ONLY_MULTIPLIER,
    CLEAN_MULTIPLIER,
)


def test_hr_manager_with_ai_keywords_gets_low_multiplier(hr_keyword_stuffer):
    """HR Manager with many AI keywords should get keyword-stuffer multiplier."""
    multiplier, flag = get_multiplier(hr_keyword_stuffer)
    assert multiplier == KEYWORD_STUFFER_MULTIPLIER
    assert flag == "KEYWORD STUFFER"


def test_honeypot_gets_zero_multiplier(honeypot_candidate):
    """A candidate with 55 years of experience should get 0.0 multiplier."""
    multiplier, flag = get_multiplier(honeypot_candidate)
    assert multiplier == HONEYPOT_MULTIPLIER
    assert flag == "HONEYPOT"


def test_honeypot_long_role_duration():
    """A candidate with a role lasting 600+ months should get 0.0 multiplier."""
    candidate = {
        "candidate_id": "c021",
        "current_title": "Engineer",
        "years_of_experience": 10,
        "skills": [],
        "career_history": [{"company": "ACME", "duration_months": 700, "description": ""}],
        "redrob_signals": {},
    }
    multiplier, flag = get_multiplier(candidate)
    assert multiplier == HONEYPOT_MULTIPLIER


def test_clean_candidate_gets_1_0_multiplier(mock_candidates):
    """The first mock candidate (strong AI engineer) should get 1.0 multiplier."""
    multiplier, flag = get_multiplier(mock_candidates[0])
    assert multiplier == CLEAN_MULTIPLIER
    assert flag is None


def test_consulting_only_gets_consulting_multiplier(consulting_only_candidate):
    """A consulting-only candidate should get the consulting multiplier."""
    multiplier, flag = get_multiplier(consulting_only_candidate)
    assert multiplier == CONSULTING_ONLY_MULTIPLIER
    assert flag == "CONSULTING ONLY"

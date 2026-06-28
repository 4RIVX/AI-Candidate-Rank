"""Experience dimension scorer.

Scores candidates on years of experience, company type (product vs consulting),
and production ML keywords found in career descriptions.
"""

import logging
from typing import Any

from src.config import (
    COMPANY_ALL_CONSULTING_SCORE,
    COMPANY_PRIMARILY_PRODUCT_SCORE,
    COMPANY_SOME_PRODUCT_SCORE,
    CONSULTING_FIRMS,
    EXPERIENCE_WEIGHT_COMPANY,
    EXPERIENCE_WEIGHT_PRODUCTION,
    EXPERIENCE_WEIGHT_YOE,
    PRODUCTION_ML_KEYWORDS,
    YOE_IDEAL_MAX,
    YOE_IDEAL_MIN,
    YOE_IDEAL_SCORE,
    YOE_LOW_SCORE,
    YOE_MID_MAX,
    YOE_MID_MIN,
    YOE_MID_SCORE,
)

logger = logging.getLogger(__name__)


def _yoe_score(years: float | None) -> float:
    """Compute years-of-experience sub-score.

    Args:
        years: Years of experience, or None if not available.

    Returns:
        A float in [0.0, 1.0].
    """
    if years is None:
        return YOE_LOW_SCORE
    years = float(years)
    if YOE_IDEAL_MIN <= years <= YOE_IDEAL_MAX:
        return YOE_IDEAL_SCORE
    if YOE_MID_MIN <= years < YOE_IDEAL_MIN or YOE_IDEAL_MAX < years <= YOE_MID_MAX:
        return YOE_MID_SCORE
    return YOE_LOW_SCORE


def _company_type_score(career_history: list[dict[str, Any]]) -> float:
    """Compute company-type sub-score based on consulting vs product company history.

    Args:
        career_history: List of career role dicts, each optionally containing 'company'.

    Returns:
        A float in [0.0, 1.0].
    """
    if not career_history:
        return COMPANY_SOME_PRODUCT_SCORE

    company_names = []
    for role in career_history:
        if isinstance(role, dict):
            company = role.get("company") or role.get("company_name") or ""
            if company:
                company_names.append(str(company).lower())

    if not company_names:
        return COMPANY_SOME_PRODUCT_SCORE

    consulting_flags = [
        any(firm in name for firm in CONSULTING_FIRMS)
        for name in company_names
    ]

    if all(consulting_flags):
        return COMPANY_ALL_CONSULTING_SCORE
    if any(not flag for flag in consulting_flags):
        if sum(not flag for flag in consulting_flags) > len(consulting_flags) / 2:
            return COMPANY_PRIMARILY_PRODUCT_SCORE
        return COMPANY_SOME_PRODUCT_SCORE
    return COMPANY_SOME_PRODUCT_SCORE


def _production_ml_score(career_history: list[dict[str, Any]]) -> float:
    """Compute production-ML keyword sub-score from career descriptions.

    Args:
        career_history: List of career role dicts, each optionally containing 'description'.

    Returns:
        A float in [0.0, 1.0].
    """
    if not career_history:
        return 0.0

    all_text = " ".join(
        str(role.get("description") or "").lower()
        for role in career_history
        if isinstance(role, dict)
    )

    matched = sum(1 for kw in PRODUCTION_ML_KEYWORDS if kw.lower() in all_text)
    return min(1.0, matched / max(len(PRODUCTION_ML_KEYWORDS), 1))


def score(candidate: dict[str, Any]) -> float:
    """Compute the experience score for a single candidate.

    Args:
        candidate: A candidate dict.

    Returns:
        A float in [0.0, 1.0].

    Raises:
        ValueError: If candidate is not a dict.
    """
    if not isinstance(candidate, dict):
        raise ValueError(f"candidate must be a dict, got {type(candidate)}")

    years = candidate.get("years_of_experience")
    career_history = candidate.get("career_history") or []

    yoe = _yoe_score(years)
    company = _company_type_score(career_history)
    production = _production_ml_score(career_history)

    final = (
        EXPERIENCE_WEIGHT_YOE * yoe
        + EXPERIENCE_WEIGHT_COMPANY * company
        + EXPERIENCE_WEIGHT_PRODUCTION * production
    )
    return float(min(1.0, max(0.0, final)))

"""Behavioral/signals dimension scorer.

Scores candidates on recency, availability, engagement, and reliability
using redrob_signals fields.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from src.config import (
    AVAILABILITY_NOTICE_PERIOD_WEIGHT,
    AVAILABILITY_OPEN_TO_WORK_WEIGHT,
    BEHAVIORAL_AVAILABILITY_WEIGHT,
    BEHAVIORAL_ENGAGEMENT_WEIGHT,
    BEHAVIORAL_RECENCY_WEIGHT,
    BEHAVIORAL_RELIABILITY_WEIGHT,
    ENGAGEMENT_GITHUB_WEIGHT,
    ENGAGEMENT_INTERVIEW_RATE_WEIGHT,
    ENGAGEMENT_RESPONSE_RATE_WEIGHT,
    GITHUB_ACTIVITY_MAX,
    GITHUB_ACTIVITY_MISSING,
    NOTICE_PERIOD_MAX_DAYS,
    OPEN_TO_WORK_FALSE_SCORE,
    OPEN_TO_WORK_TRUE_SCORE,
    RECENCY_TIER_1_DAYS,
    RECENCY_TIER_1_SCORE,
    RECENCY_TIER_2_DAYS,
    RECENCY_TIER_2_SCORE,
    RECENCY_TIER_3_DAYS,
    RECENCY_TIER_3_SCORE,
    RECENCY_TIER_4_DAYS,
    RECENCY_TIER_4_SCORE,
    RECENCY_TIER_5_SCORE,
    RELIABILITY_COMPLETENESS_WEIGHT,
    RELIABILITY_EMAIL_SCORE,
    RELIABILITY_LINKEDIN_SCORE,
    RELIABILITY_PHONE_SCORE,
)

logger = logging.getLogger(__name__)


def _parse_date(date_str: Any) -> datetime | None:
    """Parse a date string into a timezone-aware datetime.

    Args:
        date_str: A date string or None.

    Returns:
        A timezone-aware datetime, or None if parsing fails.
    """
    if not date_str:
        return None
    from dateutil.parser import parse as dateutil_parse  # type: ignore[import]
    try:
        dt = dateutil_parse(str(date_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _recency_score(signals: dict[str, Any]) -> float:
    """Compute recency sub-score from last_active_date.

    Args:
        signals: redrob_signals dict from a candidate.

    Returns:
        A float in [0.0, 1.0].
    """
    last_active = signals.get("last_active_date")
    dt = _parse_date(last_active)
    if dt is None:
        return RECENCY_TIER_4_SCORE

    now = datetime.now(timezone.utc)
    days_ago = (now - dt).days

    if days_ago <= RECENCY_TIER_1_DAYS:
        return RECENCY_TIER_1_SCORE
    if days_ago <= RECENCY_TIER_2_DAYS:
        return RECENCY_TIER_2_SCORE
    if days_ago <= RECENCY_TIER_3_DAYS:
        return RECENCY_TIER_3_SCORE
    if days_ago <= RECENCY_TIER_4_DAYS:
        return RECENCY_TIER_4_SCORE
    return RECENCY_TIER_5_SCORE


def _availability_score(signals: dict[str, Any]) -> float:
    """Compute availability sub-score from open_to_work_flag and notice_period_days.

    Args:
        signals: redrob_signals dict from a candidate.

    Returns:
        A float in [0.0, 1.0].
    """
    open_to_work = signals.get("open_to_work_flag", False)
    otw_score = OPEN_TO_WORK_TRUE_SCORE if open_to_work else OPEN_TO_WORK_FALSE_SCORE

    notice_days = signals.get("notice_period_days")
    if notice_days is None:
        notice_score = 0.5
    else:
        notice_days = max(0, float(notice_days))
        notice_score = max(0.0, 1.0 - notice_days / NOTICE_PERIOD_MAX_DAYS)

    return float(
        AVAILABILITY_OPEN_TO_WORK_WEIGHT * otw_score
        + AVAILABILITY_NOTICE_PERIOD_WEIGHT * notice_score
    )


def _engagement_score(signals: dict[str, Any]) -> float:
    """Compute engagement sub-score from response/interview rates and GitHub activity.

    Args:
        signals: redrob_signals dict from a candidate.

    Returns:
        A float in [0.0, 1.0].
    """
    response_rate = float(signals.get("recruiter_response_rate") or 0.0)
    interview_rate = float(signals.get("interview_completion_rate") or 0.0)
    github_raw = signals.get("github_activity_score", GITHUB_ACTIVITY_MISSING)
    if github_raw == GITHUB_ACTIVITY_MISSING or github_raw is None:
        github_score = 0.0
    else:
        github_score = min(float(github_raw), GITHUB_ACTIVITY_MAX) / GITHUB_ACTIVITY_MAX

    return float(
        ENGAGEMENT_RESPONSE_RATE_WEIGHT * response_rate
        + ENGAGEMENT_INTERVIEW_RATE_WEIGHT * interview_rate
        + ENGAGEMENT_GITHUB_WEIGHT * github_score
    )


def _reliability_score(signals: dict[str, Any]) -> float:
    """Compute reliability sub-score from verification flags and profile completeness.

    Args:
        signals: redrob_signals dict from a candidate.

    Returns:
        A float in [0.0, 1.0].
    """
    verified_email = RELIABILITY_EMAIL_SCORE if signals.get("verified_email") else 0.0
    verified_phone = RELIABILITY_PHONE_SCORE if signals.get("verified_phone") else 0.0
    linkedin = RELIABILITY_LINKEDIN_SCORE if signals.get("linkedin_connected") else 0.0

    completeness = float(signals.get("profile_completeness_score") or 0.0)
    completeness_score = RELIABILITY_COMPLETENESS_WEIGHT * (completeness / 100.0)

    return min(1.0, verified_email + verified_phone + linkedin + completeness_score)


def score(candidate: dict[str, Any]) -> float:
    """Compute the behavioral score for a single candidate.

    Args:
        candidate: A candidate dict.

    Returns:
        A float in [0.0, 1.0].

    Raises:
        ValueError: If candidate is not a dict.
    """
    if not isinstance(candidate, dict):
        raise ValueError(f"candidate must be a dict, got {type(candidate)}")

    signals = candidate.get("redrob_signals") or {}
    if not isinstance(signals, dict):
        signals = {}

    recency = _recency_score(signals)
    availability = _availability_score(signals)
    engagement = _engagement_score(signals)
    reliability = _reliability_score(signals)

    final = (
        BEHAVIORAL_RECENCY_WEIGHT * recency
        + BEHAVIORAL_AVAILABILITY_WEIGHT * availability
        + BEHAVIORAL_ENGAGEMENT_WEIGHT * engagement
        + BEHAVIORAL_RELIABILITY_WEIGHT * reliability
    )
    return float(min(1.0, max(0.0, final)))

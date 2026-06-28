"""Skill dimension scorer.

Scores candidates based on hard-required, nice-to-have, and penalty skills.
Also incorporates redrob_signals skill_assessment_scores when available.
"""

import logging
from typing import Any

from src.config import (
    DOMAIN_PENALTY,
    HARD_REQUIRED_SKILLS,
    HARD_SKILL_CAP,
    HARD_SKILL_VALUE,
    NICE_SKILL_CAP,
    NICE_SKILL_VALUE,
    NICE_TO_HAVE_SKILLS,
    PENALTY_ONLY_DOMAINS,
)

logger = logging.getLogger(__name__)


def _extract_skill_names(candidate: dict[str, Any]) -> list[str]:
    """Extract all skill names from a candidate dict.

    Args:
        candidate: A candidate dict.

    Returns:
        A lowercased list of skill name strings.
    """
    skill_names: list[str] = []
    skills = candidate.get("skills") or []
    for skill in skills:
        if isinstance(skill, dict):
            name = skill.get("name") or skill.get("skill_name") or ""
            if name:
                skill_names.append(str(name).lower())
        elif isinstance(skill, str):
            skill_names.append(skill.lower())
    return skill_names


def _assessment_boost(candidate: dict[str, Any]) -> float:
    """Compute a small boost from skill assessment scores in redrob_signals.

    Args:
        candidate: A candidate dict potentially containing redrob_signals.

    Returns:
        A float boost in [0.0, 0.1].
    """
    signals = candidate.get("redrob_signals") or {}
    if not isinstance(signals, dict):
        return 0.0
    assessments = signals.get("skill_assessment_scores") or {}
    if not isinstance(assessments, dict) or not assessments:
        return 0.0
    relevant_keys = HARD_REQUIRED_SKILLS + NICE_TO_HAVE_SKILLS
    relevant_scores = [
        float(v) / 100.0
        for k, v in assessments.items()
        if any(r in k.lower() for r in relevant_keys)
        and isinstance(v, (int, float))
    ]
    if not relevant_scores:
        return 0.0
    return min(0.1, sum(relevant_scores) / len(relevant_scores) * 0.1)


def score(candidate: dict[str, Any]) -> float:
    """Compute the skill score for a single candidate.

    Args:
        candidate: A candidate dict.

    Returns:
        A float in [0.0, 1.0].

    Raises:
        ValueError: If candidate is not a dict.
    """
    if not isinstance(candidate, dict):
        raise ValueError(f"candidate must be a dict, got {type(candidate)}")

    skill_names = _extract_skill_names(candidate)
    skill_text = " ".join(skill_names)

    # Also scan career descriptions for skill matches
    career_history = candidate.get("career_history") or []
    career_text = " ".join(
        str(role.get("description") or "").lower()
        for role in career_history
        if isinstance(role, dict)
    )
    full_text = skill_text + " " + career_text

    hard_score = sum(
        HARD_SKILL_VALUE
        for skill in HARD_REQUIRED_SKILLS
        if skill.lower() in full_text
    )
    hard_score = min(HARD_SKILL_CAP, hard_score)

    nice_score = sum(
        NICE_SKILL_VALUE
        for skill in NICE_TO_HAVE_SKILLS
        if skill.lower() in full_text
    )
    nice_score = min(NICE_SKILL_CAP, nice_score)

    # Penalty: if penalty domains appear and NO hard skills exist
    penalty = 0.0
    has_penalty_domain = any(d.lower() in full_text for d in PENALTY_ONLY_DOMAINS)
    has_hard_skill = any(s.lower() in full_text for s in HARD_REQUIRED_SKILLS)
    if has_penalty_domain and not has_hard_skill:
        penalty = DOMAIN_PENALTY

    assessment_boost = _assessment_boost(candidate)

    raw = hard_score + nice_score - penalty + assessment_boost
    return float(min(1.0, max(0.0, raw)))

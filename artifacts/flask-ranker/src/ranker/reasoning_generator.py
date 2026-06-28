"""Reasoning generator — produces human-readable reasoning strings for each ranked candidate.

Reasoning is grounded strictly in candidate data — no hallucination.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _get_company_type_label(career_history: list[dict[str, Any]]) -> str:
    """Infer a human-readable company-type label.

    Args:
        career_history: List of career role dicts.

    Returns:
        A short string like 'product', 'consulting', or 'mixed'.
    """
    from src.config import CONSULTING_FIRMS

    if not career_history:
        return "unknown"

    company_names = [
        str(role.get("company") or role.get("company_name") or "").lower()
        for role in career_history
        if isinstance(role, dict)
    ]
    company_names = [c for c in company_names if c]

    if not company_names:
        return "unknown"

    consulting_count = sum(
        1 for name in company_names
        if any(firm in name for firm in CONSULTING_FIRMS)
    )
    if consulting_count == len(company_names):
        return "consulting-only"
    if consulting_count == 0:
        return "product"
    return "mixed product/consulting"


def _top_skill(candidate: dict[str, Any]) -> str | None:
    """Return the most relevant hard skill from the candidate profile.

    Args:
        candidate: A candidate dict.

    Returns:
        A skill name string, or None if none found.
    """
    from src.config import HARD_REQUIRED_SKILLS

    skills = candidate.get("skills") or []
    skill_names = []
    for skill in skills:
        if isinstance(skill, dict):
            name = str(skill.get("name") or skill.get("skill_name") or "").lower()
            if name:
                skill_names.append(name)
        elif isinstance(skill, str):
            skill_names.append(skill.lower())

    for hard_skill in HARD_REQUIRED_SKILLS:
        if any(hard_skill.lower() in s for s in skill_names):
            return hard_skill

    career_history = candidate.get("career_history") or []
    career_text = " ".join(
        str(role.get("description") or "").lower()
        for role in career_history
        if isinstance(role, dict)
    )
    for hard_skill in HARD_REQUIRED_SKILLS:
        if hard_skill.lower() in career_text:
            return hard_skill

    return skill_names[0] if skill_names else None


def generate(ranked_candidate: dict[str, Any]) -> str:
    """Generate a 1-2 sentence reasoning string for a ranked candidate.

    Uses only facts from the candidate profile — never hallucinated.

    Args:
        ranked_candidate: A ranked candidate dict (output of hybrid_ranker.rank).

    Returns:
        A reasoning string of 1-2 sentences.

    Raises:
        ValueError: If ranked_candidate is not a dict.
    """
    if not isinstance(ranked_candidate, dict):
        raise ValueError(f"ranked_candidate must be a dict, got {type(ranked_candidate)}")

    parts: list[str] = []

    title = ranked_candidate.get("current_title") or ranked_candidate.get("headline")
    yoe = ranked_candidate.get("years_of_experience")
    current_company = ranked_candidate.get("current_company") or ""
    career_history = ranked_candidate.get("career_history") or []
    company_type = _get_company_type_label(career_history)

    # Opening: title + yoe + company label (prefer actual name, fall back to type)
    company_label = current_company if current_company else f"{company_type} company"
    if title and yoe is not None:
        parts.append(f"{title} with {int(yoe)}yrs at {company_label}")
    elif title and current_company:
        parts.append(f"{title} at {current_company}")
    elif title:
        parts.append(f"{title}")
    elif yoe is not None:
        parts.append(f"{int(yoe)} years of experience at {company_label}")

    # Top skill or career highlight
    top_skill = _top_skill(ranked_candidate)
    scores = ranked_candidate.get("scores") or {}

    if top_skill:
        skill_score = scores.get("skill", 0.0)
        if skill_score >= 0.6:
            parts.append(f"strong match on {top_skill}")
        else:
            parts.append(f"has {top_skill} skills")

    # Behavioral note
    signals = ranked_candidate.get("redrob_signals") or {}
    if isinstance(signals, dict):
        notice = signals.get("notice_period_days")
        open_to_work = signals.get("open_to_work_flag")
        if open_to_work:
            parts.append("actively looking")
        elif notice is not None:
            parts.append(f"{int(notice)}-day notice period")

    # Disqualifier concern
    flag = ranked_candidate.get("disqualifier_flag")
    if flag:
        flag_readable = flag.replace("_", " ").title()
        parts.append(f"flagged: {flag_readable}")

    # Semantic score note for low scorers
    semantic = scores.get("semantic", 1.0)
    if semantic < 0.3 and not flag:
        parts.append("limited JD alignment")

    sentence = "; ".join(parts) + "." if parts else "Insufficient profile data for detailed reasoning."
    return sentence

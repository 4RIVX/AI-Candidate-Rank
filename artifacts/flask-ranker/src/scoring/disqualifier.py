"""Disqualifier module — applies penalty multipliers to final scores.

Returns a multiplier in [0.0, 1.0] based on disqualifying patterns.
The most severe (lowest) multiplier wins.
"""

import logging
from typing import Any

from src.config import (
    CLEAN_MULTIPLIER,
    CONSULTING_FIRMS,
    CONSULTING_ONLY_MULTIPLIER,
    HONEYPOT_MAX_ROLE_MONTHS,
    HONEYPOT_MAX_UNRELATED_EXPERT_SKILLS,
    HONEYPOT_MAX_YOE,
    HONEYPOT_MULTIPLIER,
    INDIA_COUNTRY_VALUES,
    KEYWORD_STUFFER_AI_SKILL_THRESHOLD,
    KEYWORD_STUFFER_MULTIPLIER,
    LOCATION_PENALTY_MULTIPLIER,
    NLP_RETRIEVAL_SKILLS,
    NON_AI_JOB_TITLES,
    OFF_TARGET_SPECIALIST_MULTIPLIER,
    OFF_TARGET_TOP_SKILLS,
    PRODUCTION_KEYWORDS,
    RESEARCH_KEYWORDS,
    RESEARCH_ONLY_MULTIPLIER,
)

logger = logging.getLogger(__name__)

# AI-sounding keywords used to detect keyword stuffers
_AI_KEYWORDS: list[str] = [
    "ai", "ml", "machine learning", "deep learning", "neural", "gpt", "llm",
    "nlp", "computer vision", "data science", "tensorflow", "pytorch",
    "scikit", "embeddings", "transformer", "bert", "recommendation",
]

# Broad skill domains used for honeypot detection
_SKILL_DOMAINS: list[str] = [
    "python", "java", "javascript", "c++", "sql", "react", "angular",
    "kubernetes", "docker", "aws", "azure", "gcp", "devops", "blockchain",
    "ios", "android", "swift", "kotlin", "ruby", "go", "rust",
    "computer vision", "nlp", "speech", "robotics", "finance", "marketing",
    "accounting", "legal", "medical",
]


def _is_keyword_stuffer(candidate: dict[str, Any]) -> bool:
    """Detect keyword-stuffer pattern.

    A candidate whose title is non-AI but lists many AI keywords in skills.

    Args:
        candidate: A candidate dict.

    Returns:
        True if the keyword-stuffer pattern is detected.
    """
    title = str(candidate.get("current_title") or "").lower()
    is_non_ai_title = any(t in title for t in NON_AI_JOB_TITLES)
    if not is_non_ai_title:
        return False

    skills = candidate.get("skills") or []
    skill_text = " ".join(
        str(s.get("name") or s if isinstance(s, dict) else s).lower()
        for s in skills
    )
    ai_keyword_count = sum(1 for kw in _AI_KEYWORDS if kw in skill_text)
    return ai_keyword_count > KEYWORD_STUFFER_AI_SKILL_THRESHOLD


def _is_consulting_only(candidate: dict[str, Any]) -> bool:
    """Detect candidates whose entire career was at consulting firms.

    Args:
        candidate: A candidate dict.

    Returns:
        True if every career company is a consulting firm.
    """
    career_history = candidate.get("career_history") or []
    if not career_history:
        return False

    company_names = [
        str(role.get("company") or role.get("company_name") or "").lower()
        for role in career_history
        if isinstance(role, dict)
    ]
    company_names = [c for c in company_names if c]
    if not company_names:
        return False

    return all(
        any(firm in name for firm in CONSULTING_FIRMS)
        for name in company_names
    )


def _is_research_only(candidate: dict[str, Any]) -> bool:
    """Detect candidates who are purely research-oriented with no production experience.

    Args:
        candidate: A candidate dict.

    Returns:
        True if the profile shows research-only pattern.
    """
    career_history = candidate.get("career_history") or []
    all_text = " ".join(
        str(role.get("description") or "").lower()
        for role in career_history
        if isinstance(role, dict)
    )
    # Also check summary
    all_text += " " + str(candidate.get("summary") or "").lower()

    has_research = any(kw in all_text for kw in RESEARCH_KEYWORDS)
    has_production = any(kw in all_text for kw in PRODUCTION_KEYWORDS)
    return has_research and not has_production


def _is_honeypot(candidate: dict[str, Any]) -> bool:
    """Detect implausible/bot-like candidate profiles.

    Args:
        candidate: A candidate dict.

    Returns:
        True if the profile looks like a honeypot/spam entry.
    """
    yoe = candidate.get("years_of_experience")
    if yoe is not None and float(yoe) > HONEYPOT_MAX_YOE:
        return True

    career_history = candidate.get("career_history") or []
    for role in career_history:
        if isinstance(role, dict):
            duration = role.get("duration_months")
            if duration is not None and float(duration) > HONEYPOT_MAX_ROLE_MONTHS:
                return True

    skills = candidate.get("skills") or []
    expert_domains: set[str] = set()
    for skill in skills:
        if isinstance(skill, dict):
            proficiency = str(skill.get("proficiency") or "").lower()
            if proficiency in ("expert", "advanced"):
                name = str(skill.get("name") or "").lower()
                for domain in _SKILL_DOMAINS:
                    if domain in name:
                        expert_domains.add(domain)
    if len(expert_domains) > HONEYPOT_MAX_UNRELATED_EXPERT_SKILLS:
        return True

    return False


def _is_off_target_specialist(candidate: dict[str, Any]) -> bool:
    """Detect candidates whose primary expertise is off-target for this role.

    Applies when the candidate's top (most-listed) skill belongs to an
    irrelevant domain (e.g. Figma, OpenCV, Angular) AND they have zero
    NLP/retrieval skills anywhere in their profile.

    Args:
        candidate: A candidate dict.

    Returns:
        True if the off-target specialist pattern is detected.
    """
    skills = candidate.get("skills") or []
    skill_names: list[str] = []
    for skill in skills:
        if isinstance(skill, dict):
            name = str(skill.get("name") or skill.get("skill_name") or "").lower()
            if name:
                skill_names.append(name)
        elif isinstance(skill, str):
            skill_names.append(skill.lower())

    if not skill_names:
        return False

    # Top skill = the first listed skill (assumed most prominent)
    top_skill = skill_names[0]
    top_is_off_target = any(ot in top_skill for ot in OFF_TARGET_TOP_SKILLS)
    if not top_is_off_target:
        return False

    # Build full text for NLP/retrieval skill search (skills + career + summary)
    all_skill_text = " ".join(skill_names)
    career_history = candidate.get("career_history") or []
    career_text = " ".join(
        str(role.get("description") or "").lower()
        for role in career_history
        if isinstance(role, dict)
    )
    summary_text = str(candidate.get("summary") or "").lower()
    full_text = f"{all_skill_text} {career_text} {summary_text}"

    has_nlp_retrieval = any(kw in full_text for kw in NLP_RETRIEVAL_SKILLS)
    return not has_nlp_retrieval


def _location_penalty_applies(candidate: dict[str, Any]) -> bool:
    """Check if the location penalty should be applied.

    Args:
        candidate: A candidate dict.

    Returns:
        True if the candidate is not in India and not willing to relocate.
    """
    country = str(candidate.get("country") or candidate.get("location_country") or "").lower()
    willing = candidate.get("willing_to_relocate")

    in_india = any(val in country for val in INDIA_COUNTRY_VALUES)
    if in_india:
        return False
    if not country:
        return False
    return not willing


def get_multiplier(candidate: dict[str, Any]) -> tuple[float, str | None]:
    """Compute the disqualifier multiplier and flag label for a candidate.

    Applies the most severe (lowest) matching multiplier.

    Args:
        candidate: A candidate dict.

    Returns:
        A tuple of (multiplier, flag_label) where flag_label is None if no disqualifier.

    Raises:
        ValueError: If candidate is not a dict.
    """
    if not isinstance(candidate, dict):
        raise ValueError(f"candidate must be a dict, got {type(candidate)}")

    multiplier = CLEAN_MULTIPLIER
    flag: str | None = None

    if _is_honeypot(candidate):
        return HONEYPOT_MULTIPLIER, "HONEYPOT"

    if _is_off_target_specialist(candidate):
        if OFF_TARGET_SPECIALIST_MULTIPLIER < multiplier:
            multiplier = OFF_TARGET_SPECIALIST_MULTIPLIER
            flag = "OFF-TARGET SPECIALIST"

    if _is_keyword_stuffer(candidate):
        if KEYWORD_STUFFER_MULTIPLIER < multiplier:
            multiplier = KEYWORD_STUFFER_MULTIPLIER
            flag = "KEYWORD STUFFER"

    if _is_consulting_only(candidate):
        if CONSULTING_ONLY_MULTIPLIER < multiplier:
            multiplier = CONSULTING_ONLY_MULTIPLIER
            flag = "CONSULTING ONLY"

    if _is_research_only(candidate):
        if RESEARCH_ONLY_MULTIPLIER < multiplier:
            multiplier = RESEARCH_ONLY_MULTIPLIER
            flag = "RESEARCH ONLY"

    if _location_penalty_applies(candidate):
        multiplier *= LOCATION_PENALTY_MULTIPLIER
        if flag is None:
            flag = "LOCATION PENALTY"

    return multiplier, flag

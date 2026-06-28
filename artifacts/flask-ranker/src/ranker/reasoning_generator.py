"""Reasoning generator — produces human-readable reasoning strings for each ranked candidate.

Reasoning is grounded strictly in candidate data — no hallucination.
Rules:
  - Always reference: current_title + years_of_experience
  - Include one specific career achievement from description/summary when available
  - Include notice_period_days or open_to_work signal when present
  - Include one concern (disqualifier flag, low alignment, research-only, etc.) when applicable
  - Never use generic phrases like "has X skills"
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_ACHIEVEMENT_KEYWORDS: list[str] = [
    "built", "deployed", "led", "improved", "launched", "reduced",
    "increased", "designed", "architected", "scaled", "shipped",
    "created", "developed", "trained", "fine-tuned", "indexed",
    "served", "implemented", "established", "optimized", "achieved",
    "delivered", "automated", "migrated", "integrated", "published",
    "contributed", "founded", "grew",
]


def _extract_achievement(candidate: dict[str, Any]) -> str | None:
    """Extract one specific career achievement from descriptions or summary.

    Looks for sentences containing concrete action verbs. Prefers career
    history descriptions over the summary field.

    Args:
        candidate: A candidate dict.

    Returns:
        A trimmed achievement sentence (max 130 chars), or None if not found.
    """
    def _best_sentence(text: str) -> str | None:
        cleaned = re.sub(r"\s+", " ", text.replace("\n", ". "))
        sentences = [s.strip() for s in re.split(r"[.!?]", cleaned) if s.strip()]
        for sentence in sentences:
            sl = sentence.lower()
            if any(kw in sl for kw in _ACHIEVEMENT_KEYWORDS) and len(sentence) > 25:
                trimmed = sentence[:130]
                return trimmed + ("…" if len(sentence) > 130 else "")
        return None

    career_history = candidate.get("career_history") or []
    for role in career_history:
        if isinstance(role, dict):
            desc = str(role.get("description") or "")
            if desc:
                result = _best_sentence(desc)
                if result:
                    return result

    summary = str(candidate.get("summary") or "")
    if summary:
        return _best_sentence(summary)

    return None


def _notice_label(signals: dict[str, Any]) -> str | None:
    """Return a human-readable availability label from redrob_signals.

    Args:
        signals: The redrob_signals dict from a candidate profile.

    Returns:
        A short string like "open to work" or "30-day notice", or None.
    """
    if not isinstance(signals, dict):
        return None
    open_to_work = signals.get("open_to_work_flag")
    notice = signals.get("notice_period_days")
    if open_to_work:
        return "actively looking"
    if notice is not None:
        days = int(notice)
        if days == 0:
            return "immediate joiner"
        return f"{days}-day notice"
    return None


def _concern_label(ranked_candidate: dict[str, Any]) -> str | None:
    """Return the most relevant concern string for a candidate.

    Checks disqualifier flag first, then semantic alignment, then experience gap.

    Args:
        ranked_candidate: A ranked candidate dict.

    Returns:
        A short concern string, or None if no concern applies.
    """
    flag = ranked_candidate.get("disqualifier_flag") or (
        (ranked_candidate.get("scores") or {}).get("disqualifier_flag")
    )
    if flag:
        readable = str(flag).replace("_", " ").title()
        return f"flagged: {readable}"

    scores = ranked_candidate.get("scores") or {}

    semantic = scores.get("semantic", 1.0)
    if semantic < 0.25:
        return "low JD alignment"

    exp_score = scores.get("experience", 1.0)
    if exp_score < 0.35:
        yoe = ranked_candidate.get("years_of_experience")
        if yoe is not None:
            return f"experience gap ({int(yoe)} yrs vs 5-9 ideal)"

    skill_score = scores.get("skill", 1.0)
    if skill_score == 0.0:
        return "no matching technical skills"

    return None


def generate(ranked_candidate: dict[str, Any]) -> str:
    """Generate a 2-3 clause reasoning string for a ranked candidate.

    Structure: "{title} — {N} yrs. {achievement}. {availability}. {concern}."
    Uses only verifiable facts from the candidate profile.

    Args:
        ranked_candidate: A ranked candidate dict (output of hybrid_ranker.rank).

    Returns:
        A reasoning string.

    Raises:
        ValueError: If ranked_candidate is not a dict.
    """
    if not isinstance(ranked_candidate, dict):
        raise ValueError(f"ranked_candidate must be a dict, got {type(ranked_candidate)}")

    clauses: list[str] = []

    title = ranked_candidate.get("current_title") or ranked_candidate.get("headline")
    yoe = ranked_candidate.get("years_of_experience")
    current_company = ranked_candidate.get("current_company") or ""

    # Clause 1: title + experience + company
    if title and yoe is not None and current_company:
        clauses.append(f"{title} ({int(yoe)} yrs) at {current_company}")
    elif title and yoe is not None:
        clauses.append(f"{title} — {int(yoe)} yrs experience")
    elif title and current_company:
        clauses.append(f"{title} at {current_company}")
    elif title:
        clauses.append(title)
    elif yoe is not None:
        clauses.append(f"{int(yoe)} years of experience")

    # Clause 2: one specific achievement from their profile
    achievement = _extract_achievement(ranked_candidate)
    if achievement:
        clauses.append(achievement)

    # Clause 3: availability signal
    signals = ranked_candidate.get("redrob_signals") or {}
    notice = _notice_label(signals)
    if notice:
        clauses.append(notice)

    # Clause 4: one concern if any
    concern = _concern_label(ranked_candidate)
    if concern:
        clauses.append(concern)

    if not clauses:
        return "Insufficient profile data for detailed reasoning."

    return "; ".join(clauses) + "."

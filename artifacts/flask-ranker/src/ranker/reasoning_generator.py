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

_JD_KEYWORDS: list[str] = [
    "embeddings", "vector", "retrieval", "ranking", "deployed", "production",
    "ml", "model", "inference", "search", "nlp", "pipeline", "a/b",
    "evaluation",
]


def _score_sentence(sentence: str) -> int:
    """Count how many JD keywords appear in a sentence (case-insensitive).

    Args:
        sentence: A plain-text sentence.

    Returns:
        Integer keyword match count.
    """
    sl = sentence.lower()
    return sum(1 for kw in _JD_KEYWORDS if kw in sl)


def _extract_achievement(candidate: dict[str, Any]) -> str | None:
    """Pick the single most JD-relevant sentence from career history or summary.

    Scores every sentence across ALL career history descriptions by how many
    JD keywords it contains, then returns the highest-scoring sentence. Falls
    back to summary if career history is empty. Returns None (which the caller
    converts to the "no AI/ML experience" note) when no sentence scores > 0.

    Args:
        candidate: A candidate dict.

    Returns:
        The best-scoring sentence (max 130 chars), or None if nothing matched.
    """
    def _sentences(text: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text.replace("\n", ". "))
        return [s.strip() for s in re.split(r"[.!?]", cleaned) if len(s.strip()) > 20]

    candidates_sentences: list[tuple[int, str]] = []

    career_history = candidate.get("career_history") or []
    for role in career_history:
        if isinstance(role, dict):
            desc = str(role.get("description") or "")
            if desc:
                for sentence in _sentences(desc):
                    score = _score_sentence(sentence)
                    if score > 0:
                        candidates_sentences.append((score, sentence))

    # Fall back to summary only when career history produced nothing
    if not candidates_sentences:
        summary = str(candidate.get("summary") or "")
        if summary:
            for sentence in _sentences(summary):
                score = _score_sentence(sentence)
                if score > 0:
                    candidates_sentences.append((score, sentence))

    if not candidates_sentences:
        return None

    # Return the highest-scoring sentence, trimmed to 130 chars
    best = max(candidates_sentences, key=lambda t: t[0])[1]
    return best[:130] + ("…" if len(best) > 130 else "")


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

"""Hybrid ranker — combines all 5 scoring dimensions into a final ranked list.

final_score = (
    0.30 * semantic_score
  + 0.25 * experience_score
  + 0.25 * skill_score
  + 0.20 * behavioral_score
) * disqualifier_multiplier

Ties broken by candidate_id ascending.
"""

import logging
from typing import Any

from src.config import (
    WEIGHT_BEHAVIORAL,
    WEIGHT_EXPERIENCE,
    WEIGHT_SEMANTIC,
    WEIGHT_SKILL,
)
from src.scoring import behavioral_scorer, disqualifier, experience_scorer, skill_scorer
from src.scoring.semantic_scorer import score_candidates as semantic_score_candidates

logger = logging.getLogger(__name__)


def rank(
    candidates: list[dict[str, Any]],
    top_n: int | None = None,
) -> list[dict[str, Any]]:
    """Rank all candidates and return an annotated list sorted by final score.

    Args:
        candidates: List of candidate dicts. Must be non-empty.
        top_n: If provided, only return the top N candidates.

    Returns:
        List of result dicts, each containing:
            - All original candidate fields
            - 'scores': dict with individual and final scores
            - 'rank': integer rank (1 = best)
            - 'disqualifier_flag': str or None

    Raises:
        ValueError: If candidates is empty or not a list.
    """
    if not isinstance(candidates, list) or len(candidates) == 0:
        raise ValueError("candidates must be a non-empty list")

    logger.info("Starting hybrid ranking for %d candidates", len(candidates))

    # Semantic scoring (batch, GPU-free)
    semantic_scores = semantic_score_candidates(candidates)

    results: list[dict[str, Any]] = []
    for i, candidate in enumerate(candidates):
        sem = semantic_scores[i]
        exp = experience_scorer.score(candidate)
        ski = skill_scorer.score(candidate)
        beh = behavioral_scorer.score(candidate)
        multiplier, flag = disqualifier.get_multiplier(candidate)

        weighted = (
            WEIGHT_SEMANTIC * sem
            + WEIGHT_EXPERIENCE * exp
            + WEIGHT_SKILL * ski
            + WEIGHT_BEHAVIORAL * beh
        )
        final = weighted * multiplier

        result = dict(candidate)
        result["scores"] = {
            "semantic": round(sem, 4),
            "experience": round(exp, 4),
            "skill": round(ski, 4),
            "behavioral": round(beh, 4),
            "final": round(final, 4),
            "disqualifier_multiplier": round(multiplier, 4),
            "disqualifier_flag": flag,
        }
        result["_final_score"] = final
        result["disqualifier_flag"] = flag
        results.append(result)

    # Sort: final score descending, then candidate_id ascending (tie-break)
    results.sort(
        key=lambda r: (-r["_final_score"], str(r.get("candidate_id") or ""))
    )

    for rank_pos, result in enumerate(results, start=1):
        result["rank"] = rank_pos

    if top_n is not None and top_n > 0:
        results = results[:top_n]

    logger.info("Ranking complete. Top score: %.4f", results[0]["_final_score"] if results else 0.0)
    return results

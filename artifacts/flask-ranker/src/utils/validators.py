"""Input validation functions for the Redrob AI Ranker."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def validate_candidate(candidate: dict[str, Any], index: int) -> None:
    """Validate that a candidate dict has the required top-level field.

    Args:
        candidate: The candidate dictionary to validate.
        index: The zero-based index of the candidate in the input list.

    Raises:
        ValueError: If the candidate is missing the required candidate_id field.
    """
    if not isinstance(candidate, dict):
        raise ValueError(
            f"Candidate at index {index} must be a dict, got {type(candidate)}"
        )
    if "candidate_id" not in candidate:
        raise ValueError(
            f"Candidate at index {index} is missing required field 'candidate_id'"
        )


def validate_candidates_list(candidates: list[dict[str, Any]]) -> None:
    """Validate a list of candidate dicts.

    Args:
        candidates: List of candidate dicts to validate.

    Raises:
        ValueError: If candidates is not a list, is empty, or any entry is invalid.
    """
    if not isinstance(candidates, list):
        raise ValueError(f"candidates must be a list, got {type(candidates)}")
    if len(candidates) == 0:
        raise ValueError("candidates list is empty")
    for i, candidate in enumerate(candidates):
        validate_candidate(candidate, i)


def validate_top_n(top_n: Any) -> int:
    """Validate and coerce the top_n parameter.

    Args:
        top_n: The top_n value from the request.

    Returns:
        A valid integer top_n value.

    Raises:
        ValueError: If top_n cannot be coerced to a positive integer.
    """
    try:
        value = int(top_n)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"top_n must be an integer, got: {top_n!r}") from exc
    if value < 1:
        raise ValueError(f"top_n must be >= 1, got {value}")
    return value

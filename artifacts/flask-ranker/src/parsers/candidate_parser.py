"""Parse and validate candidate JSON/JSONL data.

Provides functions to load candidates from raw text or dict lists,
validate schema, and build text representations for embedding.
"""

import json
import logging
from typing import Any

from src.utils.validators import validate_candidates_list

logger = logging.getLogger(__name__)


def parse_candidates(raw: str) -> list[dict[str, Any]]:
    """Parse a JSON array or JSONL string into a list of candidate dicts.

    Args:
        raw: A string containing either a JSON array or newline-delimited JSON objects.

    Returns:
        A list of candidate dicts.

    Raises:
        ValueError: If the string cannot be parsed or fails validation.
    """
    if not isinstance(raw, str):
        raise ValueError(f"raw must be a string, got {type(raw)}")
    raw = raw.strip()
    if not raw:
        raise ValueError("Input is empty")

    candidates: list[dict[str, Any]] = []

    if raw.startswith("["):
        try:
            candidates = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse JSON array: {exc}") from exc
    else:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            try:
                obj = json.loads(line)
                candidates.append(obj)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Failed to parse JSONL line {i + 1}: {exc}") from exc

    validate_candidates_list(candidates)
    logger.info("Parsed %d candidates", len(candidates))
    return candidates


def load_candidates(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Load and validate a pre-parsed list of candidate dicts.

    Args:
        data: A list of candidate dicts already parsed from JSON.

    Returns:
        The validated list of candidate dicts.

    Raises:
        ValueError: If data fails validation.
    """
    validate_candidates_list(data)
    logger.info("Loaded %d candidates", len(data))
    return data


def build_text_representation(candidate: dict[str, Any]) -> str:
    """Build a single text string from a candidate for embedding.

    Concatenates: headline + summary + career_history descriptions + skill names.

    Args:
        candidate: A candidate dict.

    Returns:
        A single string representing the candidate's profile text.
    """
    parts: list[str] = []

    headline = candidate.get("headline") or candidate.get("current_title") or ""
    if headline:
        parts.append(str(headline))

    summary = candidate.get("summary") or ""
    if summary:
        parts.append(str(summary))

    career_history = candidate.get("career_history") or []
    for role in career_history:
        if isinstance(role, dict):
            description = role.get("description") or ""
            if description:
                parts.append(str(description))

    skills = candidate.get("skills") or []
    skill_names: list[str] = []
    for skill in skills:
        if isinstance(skill, dict):
            name = skill.get("name") or skill.get("skill_name") or ""
            if name:
                skill_names.append(str(name))
        elif isinstance(skill, str):
            skill_names.append(skill)
    if skill_names:
        parts.append(" ".join(skill_names))

    return " ".join(parts)

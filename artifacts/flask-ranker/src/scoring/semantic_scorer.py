"""Semantic similarity scorer — sentence-transformers only.

Model: all-MiniLM-L6-v2.
Raises ImportError at startup if sentence-transformers is not installed.
TF-IDF fallback is not used under any circumstance.
"""

import logging
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.config import JOB_DESCRIPTION, SENTENCE_TRANSFORMER_MODEL
from src.parsers.candidate_parser import build_text_representation

logger = logging.getLogger(__name__)

_model: Any = None


def _load_model() -> Any:
    """Load all-MiniLM-L6-v2 via sentence-transformers.

    Returns:
        A loaded SentenceTransformer instance.

    Raises:
        ImportError: If sentence-transformers is not installed or the model fails to load.
    """
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ModuleNotFoundError as exc:
        raise ImportError(
            "sentence-transformers is required but not installed. "
            "Install it with: pip install sentence-transformers"
        ) from exc

    logger.info("Loading sentence-transformer model: %s", SENTENCE_TRANSFORMER_MODEL)
    try:
        model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
    except Exception as exc:
        raise ImportError(
            f"Failed to load model '{SENTENCE_TRANSFORMER_MODEL}': {exc}"
        ) from exc

    logger.info("sentence-transformers model loaded successfully")
    return model


def get_model() -> Any:
    """Return the cached SentenceTransformer model, loading it on first call.

    Returns:
        A loaded SentenceTransformer instance.

    Raises:
        ImportError: If the model cannot be loaded.
    """
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def is_model_loaded() -> bool:
    """Check whether the model has been loaded into memory.

    Returns:
        True if the model is ready to score.
    """
    return _model is not None


def score_candidates(candidates: list[dict[str, Any]]) -> list[float]:
    """Score all candidates by cosine similarity to the job description embedding.

    Args:
        candidates: List of candidate dicts. Must be non-empty.

    Returns:
        A list of floats in [0.0, 1.0], one per candidate.

    Raises:
        ValueError: If candidates is empty or not a list.
        ImportError: If sentence-transformers is not installed.
    """
    if not isinstance(candidates, list) or len(candidates) == 0:
        raise ValueError("candidates must be a non-empty list")

    model = get_model()

    jd_embedding: np.ndarray = model.encode(
        [JOB_DESCRIPTION], normalize_embeddings=True
    )
    texts = [build_text_representation(c) for c in candidates]
    candidate_embeddings: np.ndarray = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    )
    sims: np.ndarray = cosine_similarity(candidate_embeddings, jd_embedding).flatten()
    scores = [float(np.clip(s, 0.0, 1.0)) for s in sims]

    logger.info("Semantic scoring complete for %d candidates", len(candidates))
    return scores

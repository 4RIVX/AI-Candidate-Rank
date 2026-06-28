"""Semantic similarity scorer — uses sentence-transformers if available, else TF-IDF.

Primary: all-MiniLM-L6-v2 via sentence-transformers (CPU).
Fallback: TF-IDF cosine similarity via scikit-learn (always available).
"""

import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import JOB_DESCRIPTION, SENTENCE_TRANSFORMER_MODEL
from src.parsers.candidate_parser import build_text_representation

logger = logging.getLogger(__name__)

_model: Any = None
_use_sentence_transformers: bool = False


def _try_load_sentence_transformers() -> bool:
    """Attempt to load the sentence-transformers model.

    Returns:
        True if loaded successfully, False otherwise.
    """
    global _model, _use_sentence_transformers
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        logger.info("Loading sentence-transformer model: %s", SENTENCE_TRANSFORMER_MODEL)
        _model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        _use_sentence_transformers = True
        logger.info("sentence-transformers model loaded successfully")
        return True
    except (ImportError, Exception) as exc:
        logger.warning(
            "sentence-transformers not available (%s), falling back to TF-IDF cosine similarity",
            exc,
        )
        _use_sentence_transformers = False
        return False


def get_model() -> Any:
    """Load and cache the model (sentence-transformers or TF-IDF fallback).

    Returns:
        The loaded model or None if using TF-IDF.
    """
    global _model, _use_sentence_transformers
    if _model is None and not _use_sentence_transformers:
        _try_load_sentence_transformers()
    return _model


def is_model_loaded() -> bool:
    """Check if the model (or fallback) has been initialised.

    Returns:
        True once scoring is ready.
    """
    return _use_sentence_transformers or _model is not None


def _tfidf_score_candidates(candidates: list[dict[str, Any]]) -> list[float]:
    """Score candidates using TF-IDF cosine similarity (fallback).

    Args:
        candidates: List of candidate dicts.

    Returns:
        List of floats in [0.0, 1.0].
    """
    texts = [build_text_representation(c) for c in candidates]
    all_texts = [JOB_DESCRIPTION] + texts

    vectorizer = TfidfVectorizer(
        sublinear_tf=True,
        ngram_range=(1, 2),
        max_features=10000,
        stop_words="english",
    )
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    jd_vec = tfidf_matrix[0]
    candidate_vecs = tfidf_matrix[1:]

    sims = cosine_similarity(candidate_vecs, jd_vec).flatten()
    return [float(np.clip(s, 0.0, 1.0)) for s in sims]


def score_candidates(candidates: list[dict[str, Any]]) -> list[float]:
    """Score all candidates by semantic similarity to the job description.

    Uses sentence-transformers when available, TF-IDF cosine similarity otherwise.

    Args:
        candidates: List of candidate dicts. Each must be a non-empty dict.

    Returns:
        A list of floats in [0.0, 1.0], one per candidate.

    Raises:
        ValueError: If candidates is empty or not a list.
    """
    if not isinstance(candidates, list) or len(candidates) == 0:
        raise ValueError("candidates must be a non-empty list")

    # Ensure model initialised
    get_model()

    if _use_sentence_transformers and _model is not None:
        jd_embedding: np.ndarray = _model.encode(
            [JOB_DESCRIPTION], normalize_embeddings=True
        )
        texts = [build_text_representation(c) for c in candidates]
        candidate_embeddings: np.ndarray = _model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )
        sims: np.ndarray = cosine_similarity(candidate_embeddings, jd_embedding).flatten()
        scores = [float(np.clip(s, 0.0, 1.0)) for s in sims]
    else:
        scores = _tfidf_score_candidates(candidates)

    logger.info(
        "Semantic scoring complete for %d candidates (backend=%s)",
        len(candidates),
        "sentence-transformers" if _use_sentence_transformers else "tfidf",
    )
    return scores

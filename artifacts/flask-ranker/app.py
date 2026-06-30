"""Flask API server for the Redrob AI Candidate Ranker.

Endpoints:
  GET  /api/healthz           — health check
  GET  /api/rank/status       — ML model readiness
  POST /api/rank              — rank candidates (JSON body)
"""

import io
import csv
import logging
import time
from typing import Any

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from src.parsers.candidate_parser import load_candidates
from src.ranker import hybrid_ranker, reasoning_generator
from src.scoring import semantic_scorer
from src.utils.validators import validate_candidates_list, validate_top_n

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.get("/api/healthz")
def health_check() -> tuple[Response, int]:
    """Health check endpoint.

    Returns:
        JSON with status and model load state.
    """
    return (
        jsonify(
            {
                "status": "ok",
                "python_backend": "flask",
                "model_loaded": semantic_scorer.is_model_loaded(),
            }
        ),
        200,
    )


@app.get("/api/rank/status")
def get_ranking_status() -> tuple[Response, int]:
    """Return the ML model readiness status.

    Returns:
        JSON with ready flag, model_loaded, and model_name.
    """
    loaded = semantic_scorer.is_model_loaded()
    return (
        jsonify(
            {
                "ready": loaded,
                "model_loaded": loaded,
                "model_name": "all-MiniLM-L6-v2",
                "message": (
                    "Model ready"
                    if loaded
                    else "Model not yet loaded — will load on first rank request"
                ),
            }
        ),
        200,
    )


@app.post("/api/rank")
def rank_candidates() -> tuple[Response, int]:
    """Rank a list of candidate dicts.

    Expects JSON body: { "candidates": [...], "top_n": 25 }

    Returns:
        JSON RankResponse with candidates, stats, and processing_time_seconds.
    """
    try:
        body = request.get_json(force=True, silent=True)
        if body is None:
            return jsonify({"error": "Request body must be JSON", "detail": None}), 400

        raw_candidates = body.get("candidates")
        if raw_candidates is None:
            return (
                jsonify(
                    {
                        "error": "Missing 'candidates' field in request body",
                        "detail": None,
                    }
                ),
                400,
            )

        top_n_raw = body.get("top_n", 25)
        try:
            top_n = validate_top_n(top_n_raw)
        except ValueError as exc:
            return jsonify({"error": str(exc), "detail": None}), 400

        try:
            candidates = load_candidates(raw_candidates)
        except ValueError as exc:
            return jsonify({"error": str(exc), "detail": None}), 400

        profiles_loaded = len(candidates)
        start = time.time()

        ranked = hybrid_ranker.rank(candidates, top_n=None)

        elapsed = time.time() - start

        # Attach reasoning
        for result in ranked:
            result["reasoning"] = reasoning_generator.generate(result)

        disqualified_count = sum(
            1 for r in ranked if r.get("disqualifier_flag") is not None
        )

        all_scores = [r["_final_score"] for r in ranked]
        top_score = max(all_scores) if all_scores else 0.0

        score_distribution = _build_score_distribution(all_scores)

        # Trim to top_n for response
        display_ranked = ranked[:top_n]

        response_candidates = []
        for r in display_ranked:
            response_candidates.append(
                {
                    "rank": r["rank"],
                    "candidate_id": str(r.get("candidate_id") or ""),
                    "current_title": r.get("current_title") or r.get("headline"),
                    "current_company": _get_current_company(r),
                    "years_of_experience": r.get("years_of_experience"),
                    "location": r.get("location") or r.get("city"),
                    "willing_to_relocate": r.get("willing_to_relocate"),
                    "score": round(r["_final_score"], 4),
                    "scores": r["scores"],
                    "reasoning": r["reasoning"],
                }
            )

        return (
            jsonify(
                {
                    "candidates": response_candidates,
                    "stats": {
                        "profiles_loaded": profiles_loaded,
                        "candidates_ranked": len(ranked),
                        "top_score": round(top_score, 4),
                        "disqualified_count": disqualified_count,
                        "score_distribution": score_distribution,
                    },
                    "processing_time_seconds": round(elapsed, 2),
                }
            ),
            200,
        )

    except Exception as exc:
        logger.error("Unexpected error in /api/rank: %s", exc, exc_info=True)
        return jsonify({"error": "Internal server error", "detail": str(exc)}), 500


@app.post("/api/rank/download")
def download_ranked_csv() -> Response | tuple[Response, int]:
    """Download ranked candidates as CSV in submission format.

    Expects same JSON body as /api/rank.

    Returns:
        CSV file download with columns: candidate_id, rank, score, reasoning.
    """
    try:
        body = request.get_json(force=True, silent=True)
        if body is None:
            return jsonify({"error": "Request body must be JSON", "detail": None}), 400

        raw_candidates = body.get("candidates")
        if raw_candidates is None:
            return (
                jsonify(
                    {
                        "error": "Missing 'candidates' field in request body",
                        "detail": None,
                    }
                ),
                400,
            )

        try:
            candidates = load_candidates(raw_candidates)
        except ValueError as exc:
            return jsonify({"error": str(exc), "detail": None}), 400

        ranked = hybrid_ranker.rank(candidates, top_n=None)
        for result in ranked:
            result["reasoning"] = reasoning_generator.generate(result)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for r in ranked:
            writer.writerow(
                [
                    r.get("candidate_id", ""),
                    r["rank"],
                    round(r["_final_score"], 4),
                    r.get("reasoning", ""),
                ]
            )

        csv_content = output.getvalue()
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=ranked_candidates.csv"
            },
        )

    except Exception as exc:
        logger.error("Unexpected error in /api/rank/download: %s", exc, exc_info=True)
        return jsonify({"error": "Internal server error", "detail": str(exc)}), 500


def _get_current_company(candidate: dict[str, Any]) -> str | None:
    """Extract the most recent company name from a candidate dict.

    Args:
        candidate: A candidate dict.

    Returns:
        Company name string or None.
    """
    career_history = candidate.get("career_history") or []
    if career_history and isinstance(career_history[0], dict):
        return career_history[0].get("company") or career_history[0].get("company_name")
    return candidate.get("current_company")


def _build_score_distribution(scores: list[float]) -> list[dict[str, Any]]:
    """Build a score distribution histogram with 10 buckets.

    Args:
        scores: List of final scores.

    Returns:
        List of {range, count} dicts.
    """
    buckets = [
        {"range": "0.0-0.1", "count": 0},
        {"range": "0.1-0.2", "count": 0},
        {"range": "0.2-0.3", "count": 0},
        {"range": "0.3-0.4", "count": 0},
        {"range": "0.4-0.5", "count": 0},
        {"range": "0.5-0.6", "count": 0},
        {"range": "0.6-0.7", "count": 0},
        {"range": "0.7-0.8", "count": 0},
        {"range": "0.8-0.9", "count": 0},
        {"range": "0.9-1.0", "count": 0},
    ]
    for s in scores:
        idx = min(int(s * 10), 9)
        buckets[idx]["count"] += 1
    return buckets


if __name__ == "__main__":
    import os

    port = int(os.environ.get("FLASK_PORT", 5001))
    logger.info("Starting Flask Ranker on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)

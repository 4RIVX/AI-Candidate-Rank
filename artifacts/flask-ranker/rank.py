"""CLI entry point for the Redrob AI Candidate Ranker.

Usage:
    python rank.py --candidates candidates.json --out output.csv
    python rank.py --candidates candidates.jsonl --out output.csv --top-n 50
"""

import argparse
import csv
import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run the CLI ranking pipeline.

    Returns:
        Exit code (0 = success, 1 = failure).
    """
    parser = argparse.ArgumentParser(
        description="Redrob AI Candidate Ranker — ranks candidates for a Senior AI Engineer role."
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to a JSON array or JSONL file of candidates.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV file path.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Return only top N ranked candidates (default: all).",
    )
    args = parser.parse_args()

    from src.parsers.candidate_parser import parse_candidates
    from src.ranker import hybrid_ranker, reasoning_generator

    try:
        with open(args.candidates, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as exc:
        logger.error("Failed to read candidates file: %s", exc)
        return 1

    try:
        candidates = parse_candidates(raw)
    except ValueError as exc:
        logger.error("Failed to parse candidates: %s", exc)
        return 1

    logger.info("Loaded %d candidates", len(candidates))
    start = time.time()

    try:
        ranked = hybrid_ranker.rank(candidates, top_n=args.top_n)
    except Exception as exc:
        logger.error("Ranking failed: %s", exc, exc_info=True)
        return 1

    for result in ranked:
        result["reasoning"] = reasoning_generator.generate(result)

    elapsed = time.time() - start
    logger.info("Ranking complete in %.2fs", elapsed)

    try:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for r in ranked:
                writer.writerow([
                    r.get("candidate_id", ""),
                    r["rank"],
                    round(r["_final_score"], 4),
                    r.get("reasoning", ""),
                ])
    except OSError as exc:
        logger.error("Failed to write output file: %s", exc)
        return 1

    logger.info("Results written to %s (%d candidates)", args.out, len(ranked))
    return 0


if __name__ == "__main__":
    sys.exit(main())

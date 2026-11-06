"""Evaluate recommendation retrieval against hand-curated relevance cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.schemas import RecommendationEvent
from app.services.event_based_recommender import get_recommendations_from_events


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate recommendation retrieval quality.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("evaluation/cases.json"),
        help="JSON file containing hand-curated relevance cases.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Recommendations evaluated per case.")
    parser.add_argument(
        "--min-mean-recall",
        type=float,
        default=0.5,
        help="Minimum mean recall@limit required for success.",
    )
    return parser.parse_args()


def evaluate(cases: list[dict[str, object]], limit: int) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for case in cases:
        name = case.get("name")
        events = case.get("events")
        relevant_movie_ids = case.get("relevant_movie_ids")
        if not isinstance(name, str) or not isinstance(events, list) or not isinstance(relevant_movie_ids, list):
            raise ValueError("each evaluation case needs name, events, and relevant_movie_ids")
        if not relevant_movie_ids or not all(isinstance(movie_id, str) for movie_id in relevant_movie_ids):
            raise ValueError(f"case {name!r} has no valid relevant_movie_ids")

        request_events = [RecommendationEvent.model_validate(event) for event in events]
        recommendations = get_recommendations_from_events(request_events, limit)
        relevant = set(relevant_movie_ids)
        hits = [movie_id for movie_id in recommendations if movie_id in relevant]
        results.append(
            {
                "name": name,
                "recommendations": recommendations,
                "relevant_hits": hits,
                "recall_at_k": len(hits) / len(relevant),
            }
        )

    mean_recall = sum(result["recall_at_k"] for result in results) / len(results)
    return {"case_count": len(results), "mean_recall_at_k": mean_recall, "cases": results}


def main() -> int:
    arguments = parse_arguments()
    if arguments.limit < 1:
        raise ValueError("limit must be at least 1")
    if not 0 <= arguments.min_mean_recall <= 1:
        raise ValueError("min-mean-recall must be between 0 and 1")

    payload = json.loads(arguments.cases.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("cases"), list):
        raise ValueError("evaluation file must contain schema_version 1 and a cases list")

    report = evaluate(payload["cases"], arguments.limit)
    print(json.dumps(report, indent=2))
    if report["mean_recall_at_k"] < arguments.min_mean_recall:
        print("Evaluation failed: mean recall is below the required threshold.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        sys.exit(1)

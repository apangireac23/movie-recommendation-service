import unittest
from unittest.mock import patch

import numpy as np
from pydantic import ValidationError

from app.api.schemas import EventsRecommendationRequest, RecommendationEvent
from app.ml.faiss_index import ArtifactNotReadyError
from app.services.event_based_recommender import get_recommendations_from_events


class FakeFaissEngine:
    def __init__(self, vectors: list[list[float]]):
        self.vectors = [np.asarray(vector, dtype="float32") for vector in vectors]
        self.ntotal = len(vectors)

    def reconstruct(self, position: int) -> np.ndarray:
        return self.vectors[position]


class FakeArtifact:
    def __init__(self, movie_ids: list[str], vectors: list[list[float]], candidates: list[str]):
        self.id_map = movie_ids
        self.index = FakeFaissEngine(vectors)
        self.candidates = candidates
        self.is_ready = True
        self.unavailable_reason = None

    def search(self, query_vector: np.ndarray, k: int) -> list[str]:
        return self.candidates[:k]


class RecommendationTests(unittest.TestCase):
    def test_removes_seen_movies_and_duplicates(self):
        artifact = FakeArtifact(
            ["seed", "one", "two", "three"],
            [[1, 0], [0.9, 0.1], [0.8, 0.2], [0.7, 0.3]],
            ["seed", "one", "one", "two", "three"],
        )
        events = [RecommendationEvent(movie_id="seed", event_type="like")]

        with patch("app.services.event_based_recommender.faiss_index", artifact):
            recommendations = get_recommendations_from_events(events, limit=2)

        self.assertEqual(recommendations, ["one", "two"])

    def test_unknown_events_return_no_recommendations(self):
        artifact = FakeArtifact(["known"], [[1, 0]], ["known"])
        events = [RecommendationEvent(movie_id="unknown", event_type="like")]

        with patch("app.services.event_based_recommender.faiss_index", artifact):
            recommendations = get_recommendations_from_events(events, limit=10)

        self.assertEqual(recommendations, [])

    def test_zero_taste_vector_returns_no_recommendations(self):
        artifact = FakeArtifact(["seed", "other"], [[1, 0], [0, 1]], ["other"])
        events = [
            RecommendationEvent(movie_id="seed", event_type="watch"),
            RecommendationEvent(movie_id="seed", event_type="skip"),
        ]

        with patch("app.services.event_based_recommender.faiss_index", artifact):
            recommendations = get_recommendations_from_events(events, limit=10)

        self.assertEqual(recommendations, [])

    def test_unavailable_artifact_returns_clear_error(self):
        artifact = FakeArtifact(["seed"], [[1, 0]], ["seed"])
        artifact.is_ready = False
        artifact.unavailable_reason = "manifest is missing"
        events = [RecommendationEvent(movie_id="seed", event_type="like")]

        with patch("app.services.event_based_recommender.faiss_index", artifact):
            with self.assertRaisesRegex(ArtifactNotReadyError, "manifest is missing"):
                get_recommendations_from_events(events, limit=10)


class RequestValidationTests(unittest.TestCase):
    def test_rejects_unsupported_event_type(self):
        with self.assertRaises(ValidationError):
            EventsRecommendationRequest.model_validate(
                {"events": [{"movie_id": "seed", "event_type": "rate"}]}
            )

    def test_rejects_out_of_range_limit(self):
        with self.assertRaises(ValidationError):
            EventsRecommendationRequest.model_validate({"events": [], "limit": 51})

"""Database-free recommendation flow for caller-supplied user events.

The movie catalogue remains in the shared FAISS index.  FAISS stores vectors
by position and ``id_map`` links each position to a movie id, so this module
can reconstruct the embeddings needed to calculate a taste vector without
querying PostgreSQL.
"""

import numpy as np

from app.core.constants import FAISS_CANDIDATES
from app.core.event_weights import EVENT_WEIGHTS
from app.core.runtime_store import faiss_index
from app.ml.faiss_index import ArtifactNotReadyError


def get_recommendations_from_events(events, limit: int):
    """Return recommendations from events supplied in the current request.

    Unknown movie ids are ignored. An empty or unusable event list returns an
    empty result.
    """
    if not faiss_index.is_ready:
        raise ArtifactNotReadyError(
            f"recommendation artifacts are not ready: {faiss_index.unavailable_reason}"
        )

    id_to_position = {
        movie_id: position
        for position, movie_id in enumerate(faiss_index.id_map)
    }

    vectors = []
    weights = []
    seen_movie_ids = set()

    for event in events:
        seen_movie_ids.add(event.movie_id)
        position = id_to_position.get(event.movie_id)
        weight = EVENT_WEIGHTS.get(event.event_type, 0)

        if position is None or position >= faiss_index.index.ntotal or weight == 0:
            continue

        vectors.append(faiss_index.index.reconstruct(position))
        weights.append(weight)

    if not vectors:
        return []

    vector_matrix = np.asarray(vectors, dtype="float32")
    weight_vector = np.asarray(weights, dtype="float32")
    taste_vector = np.sum(vector_matrix * weight_vector[:, np.newaxis], axis=0)

    norm = np.linalg.norm(taste_vector)
    if norm == 0:
        return []

    taste_vector = taste_vector / norm
    candidate_count = min(
        len(faiss_index.id_map),
        max(FAISS_CANDIDATES, limit + len(seen_movie_ids)),
    )
    candidates = faiss_index.search(taste_vector, k=candidate_count)

    recommendations = []
    for movie_id in candidates:
        if movie_id in seen_movie_ids or movie_id in recommendations:
            continue

        recommendations.append(movie_id)
        if len(recommendations) == limit:
            break

    return recommendations

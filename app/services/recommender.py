import numpy as np

from app.core.constants import FAISS_CANDIDATES, TOP_K
from app.core.event_weights import EVENT_WEIGHTS


def _build_seed_movie_ids(req):
    seed_movie_ids = []

    if req.movie_id:
        seed_movie_ids.append(req.movie_id)

    for movie_id in req.seed_movie_ids:
        if movie_id not in seed_movie_ids:
            seed_movie_ids.append(movie_id)

    return seed_movie_ids


def _compute_taste_vector(req, runtime_store):
    vectors = []
    weights = []
    seen_movie_ids = set()

    if not req.interactions:
        return None, seen_movie_ids, "no_interactions"

    for interaction in req.interactions:
        movie_vector = runtime_store.movie_vectors.get(interaction.movie_id)
        weight = EVENT_WEIGHTS.get(interaction.event_type, 0)

        if movie_vector is None or weight == 0:
            continue

        vectors.append(movie_vector)
        weights.append(weight)
        seen_movie_ids.add(interaction.movie_id)

    if not vectors:
        return None, seen_movie_ids, "no_valid_interactions"

    query_vector = np.average(np.array(vectors), axis=0, weights=np.array(weights))

    norm = np.linalg.norm(query_vector)
    if norm == 0:
        return None, seen_movie_ids, "zero_taste_vector"

    return query_vector.astype("float32"), seen_movie_ids, None


def get_recommendations(req, runtime_store):
    seed_movie_ids = _build_seed_movie_ids(req)
    taste_vector, seen_movie_ids, taste_failure_reason = _compute_taste_vector(req, runtime_store)

    if taste_vector is not None:
        excluded_ids = seen_movie_ids.union(seed_movie_ids)
        recommendations = runtime_store.search(
            query_vector=taste_vector,
            excluded_ids=excluded_ids,
            top_k=TOP_K,
            search_k=FAISS_CANDIDATES,
        )
        strategy = "taste_vector"
    else:
        print(
            "[RECOMMENDER] "
            f"user={req.user_id} "
            f"taste_computation=skipped "
            f"reason={taste_failure_reason}"
        )

        recommendations = runtime_store.recommend(
            seed_movie_ids=seed_movie_ids,
            top_k=TOP_K,
            search_k=FAISS_CANDIDATES,
        )
        strategy = "seeds" if seed_movie_ids else "fallback"

    print(
        "[RECOMMENDER] "
        f"user={req.user_id} "
        f"strategy={strategy} "
        f"taste_computed={taste_vector is not None} "
        f"interaction_count={len(req.interactions)} "
        f"seed_count={len(seed_movie_ids)} "
        f"results={len(recommendations)}"
    )

    return recommendations

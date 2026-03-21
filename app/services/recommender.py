from app.core.constants import FAISS_CANDIDATES, TOP_K


def _build_seed_movie_ids(req):
    seed_movie_ids = []

    if req.movie_id:
        seed_movie_ids.append(req.movie_id)

    for movie_id in req.seed_movie_ids:
        if movie_id not in seed_movie_ids:
            seed_movie_ids.append(movie_id)

    return seed_movie_ids


def get_recommendations(req, runtime_store):
    seed_movie_ids = _build_seed_movie_ids(req)
    recommendations = runtime_store.recommend(
        seed_movie_ids=seed_movie_ids,
        top_k=TOP_K,
        search_k=FAISS_CANDIDATES,
    )

    print(
        "[RECOMMENDER] "
        f"user={req.user_id} "
        f"seed_count={len(seed_movie_ids)} "
        f"results={len(recommendations)}"
    )

    return recommendations

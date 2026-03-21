import numpy as np
from app.services.taste_service import compute_user_taste
from app.ml.faiss_index import FaissIndex
from app.repositories.event_repository import EventRepository
from app.core.constants import TOP_K, FAISS_CANDIDATES, POPULARITY_POOL

faiss_index = FaissIndex()


def get_recommendations(user_id, db):

    decision_path = []

    # --- Step 1: Check FAISS readiness ---
    if len(faiss_index.id_map) == 0:
        decision_path.append("faiss_not_ready")
        return fallback_only(user_id, db, decision_path)

    # --- Step 2: Compute taste ---
    taste_vector = compute_user_taste(db, user_id)

    if taste_vector is None:
        decision_path.append("no_user_history")
        return fallback_only(user_id, db, decision_path)

    # --- Step 3: Normalize ---
    norm = np.linalg.norm(taste_vector)
    if norm == 0:
        decision_path.append("zero_vector")
        return fallback_only(user_id, db, decision_path)

    taste_vector = taste_vector / norm

    # --- Step 4: FAISS retrieval ---
    candidates = faiss_index.search(taste_vector, k=FAISS_CANDIDATES)
    decision_path.append("faiss_used")

    # --- Step 5: Remove seen ---
    events = EventRepository.get_user_events(db, user_id)
    seen = set(e.movie_id for e in events)

    filtered = [m for m in candidates if m not in seen]

    # --- Step 6: Primary selection ---
    primary = filtered[:TOP_K]

    # --- Step 7: Fill with fallback if needed ---
    if len(primary) < TOP_K:
        decision_path.append("fallback_fill")

        remaining = TOP_K - len(primary)

        popular = EventRepository.get_popular_movies(db, POPULARITY_POOL)

        fallback = [
            m for m in popular
            if m not in seen and m not in primary
        ]

        primary.extend(fallback[:remaining])

    # --- Step 8: Final trim ---
    final = primary[:TOP_K]

    # --- Step 9: Logging ---
    print(f"[RECOMMENDER] user={user_id} path={decision_path} results={len(final)}")

    return final


def fallback_only(user_id, db, decision_path):

    decision_path.append("fallback_only")

    popular = EventRepository.get_popular_movies(db, TOP_K)

    print(f"[RECOMMENDER] user={user_id} path={decision_path}")

    return popular



# import numpy as np
# from app.services.taste_service import compute_user_taste
# from app.ml.faiss_index import FaissIndex
# from app.repositories.event_repository import EventRepository

# faiss_index = FaissIndex()


# def get_recommendations(user_id, db):

#     # 1. compute taste vector
#     taste_vector = compute_user_taste(db, user_id)

#     if taste_vector is None:
#         return []

#     # 2. normalize (IMPORTANT)
#     norm = np.linalg.norm(taste_vector)
#     if norm == 0:
#         return []

#     taste_vector = taste_vector / norm

#     # 3. search FAISS
#     candidate_ids = faiss_index.search(taste_vector, k=20)

#     # 4. remove already seen movies
#     events = EventRepository.get_user_events(db, user_id)
#     seen_movies = set(e.movie_id for e in events)

#     recommendations = [
#         movie_id for movie_id in candidate_ids
#         if movie_id not in seen_movies
#     ]

#     return recommendations[:10]  # return top 10
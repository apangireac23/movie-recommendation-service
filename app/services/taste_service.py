import numpy as np
from app.repositories.event_repository import EventRepository
from app.repositories.movie_repository import MovieRepository
from app.core.event_weights import EVENT_WEIGHTS


def compute_user_taste(db, user_id):

    events = EventRepository.get_user_events(db, user_id)

    vectors = []
    weights = []

    for event in events:

        movie = MovieRepository.get_movie_by_id(db, event.movie_id)

        if movie and movie.embedding:

            weight = EVENT_WEIGHTS.get(event.event_type, 0)

            vectors.append(np.array(movie.embedding))
            weights.append(weight)

    if not vectors:
        return None

    vectors = np.array(vectors)
    weights = np.array(weights)

    taste_vector = np.average(vectors, axis=0, weights=weights)

    return taste_vector
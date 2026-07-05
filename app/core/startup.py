"""Service startup hooks.

Currently contains a single helper that rebuilds the in-memory FAISS index
from movie embeddings persisted in Postgres. This runs on every boot so
that a fresh deploy (with an empty `app/data/` directory) can still serve
real recommendations, as long as movies with embeddings exist in the DB.
"""

import logging

from app.core.database import SessionLocal
from app.ml.faiss_index import FaissIndex
from app.models.movie import Movie

logger = logging.getLogger(__name__)


def rebuild_faiss_from_db(faiss_index: FaissIndex) -> int:
    """Reload the FAISS index from `movies.embedding` in Postgres.

    `FaissIndex.add_movie` is idempotent (skips existing ids), so this is
    safe to run on every boot — it will only encode new movies on top of
    whatever is already in the on-disk index.

    Returns the number of movies added in this run (0 if the on-disk
    index already covered everything).
    """
    db = SessionLocal()
    added = 0
    try:
        rows = (
            db.query(Movie)
            .filter(Movie.embedding.isnot(None))
            .all()
        )
        for movie in rows:
            embedding = movie.embedding
            if embedding is None:
                continue
            # JSONB comes back as a list; FaissIndex.add_movie will cast it.
            faiss_index.add_movie(movie.id, embedding)
            added += 1

        # Persist so subsequent restarts hit the on-disk cache.
        if added:
            faiss_index.save()
    except Exception:
        # Never block service start on a DB hiccup — the recommender will
        # surface the empty index as a 503 if the rebuild failed.
        logger.exception("[STARTUP] FAISS rebuild from DB failed")
        return 0
    finally:
        db.close()

    logger.info("[STARTUP] indexed %d movies from db", added)
    return added

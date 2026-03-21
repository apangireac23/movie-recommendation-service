from app.core.database import SessionLocal
from app.services.event_service import log_user_event

events = [
  {"user_id": "u1", "movie_id": "tmdb_27205", "event_type": "like"},   # Inception
  {"user_id": "u1", "movie_id": "tmdb_157336", "event_type": "like"},  # Interstellar
  {"user_id": "u1", "movie_id": "tmdb_603", "event_type": "watch"},    # The Matrix
  {"user_id": "u1", "movie_id": "tmdb_11", "event_type": "watch"},     # Star Wars
  {"user_id": "u1", "movie_id": "tmdb_862", "event_type": "skip"},      # Toy Story
  {"user_id": "u2", "movie_id": "tmdb_299536", "event_type": "like"},  # Avengers
  {"user_id": "u2", "movie_id": "tmdb_284054", "event_type": "like"},  # Black Panther
  {"user_id": "u2", "movie_id": "tmdb_99861", "event_type": "watch"},  # Avengers 2
  {"user_id": "u2", "movie_id": "tmdb_271110", "event_type": "watch"}, # Captain America
  {"user_id": "u2", "movie_id": "tmdb_597", "event_type": "skip"},      # Titanic
  {"user_id": "u3", "movie_id": "tmdb_550", "event_type": "like"},     # Fight Club
  {"user_id": "u3", "movie_id": "tmdb_13", "event_type": "watch"},     # Forrest Gump
  {"user_id": "u3", "movie_id": "tmdb_680", "event_type": "like"},     # Pulp Fiction
  {"user_id": "u3", "movie_id": "tmdb_155", "event_type": "watch"},    # Dark Knight
  {"user_id": "u3", "movie_id": "tmdb_12", "event_type": "skip"}       # Finding Nemo
]

db = SessionLocal()

for e in events:
    log_user_event(db, type("obj", (), e))  # quick hack

db.close()
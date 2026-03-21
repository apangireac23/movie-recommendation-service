from app.ml.faiss_index import FaissIndex
from app.repositories.movie_repository import MovieRepository

faiss_index = FaissIndex()


def ingest_movie(db, movie_data):
    embedding = None

    if movie_data.plot:
        from app.ml.embedding_model import generate_embedding

        embedding = generate_embedding(movie_data.plot)

        if embedding is not None:
            faiss_index.add_movie(movie_data.id, embedding)


    # store metadata in postgres
    movie = MovieRepository.upsert_movie_with_embedding(db, movie_data, embedding)

    return movie

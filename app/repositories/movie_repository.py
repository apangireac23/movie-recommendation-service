from sqlalchemy.orm import Session
from app.models.movie import Movie


class MovieRepository:
    @staticmethod
    def _serialize_embedding(embedding):
        if embedding is None:
            return None

        if hasattr(embedding, "tolist"):
            return embedding.tolist()

        return embedding

    @staticmethod
    def get_movie_by_id(db: Session, movie_id: str):
        return db.query(Movie).filter(Movie.id == movie_id).first()

    @staticmethod
    def upsert_movie(db: Session, movie_data):
        
        movie = db.query(Movie).filter(Movie.id == movie_data.id).first()

        if movie:
            movie.title = movie_data.title
            movie.plot = movie_data.plot
            movie.genre = movie_data.genre
            movie.embedding = movie_data.embedding
        else:
            movie = Movie(
                id=movie_data.id,
                title=movie_data.title,
                plot=movie_data.plot,
                genre=movie_data.genre,
                embedding=None
            )
            db.add(movie)

        db.commit()
        db.refresh(movie)

        return movie
    
    @staticmethod
    def upsert_movie_with_embedding(db: Session, movie_data, embedding):
        def get_attr(data, attr, default=None):
            # Supports both object-style and dict-style access
            try:
                return getattr(data, attr)
            except AttributeError:
                if isinstance(data, dict):
                    return data.get(attr, default)
                return default

        movie_id = get_attr(movie_data, "id")
        if movie_id is None:
            raise ValueError("movie_data must contain an 'id'")

        serialized_embedding = MovieRepository._serialize_embedding(embedding)

        movie = db.query(Movie).filter(Movie.id == movie_id).first()

        if movie:
            movie.title = get_attr(movie_data, "title", movie.title)
            movie.plot = get_attr(movie_data, "plot", movie.plot)
            movie.genre = get_attr(movie_data, "genre", movie.genre)
            movie.embedding = serialized_embedding
        else:
            movie = Movie(
                id=movie_id,
                title=get_attr(movie_data, "title"),
                plot=get_attr(movie_data, "plot"),
                genre=get_attr(movie_data, "genre"),
                embedding=serialized_embedding
            )
            db.add(movie)

        db.commit()
        db.refresh(movie)   

        return movie
    
    
    # def upsert_movie_with_embedding(db: Session, movie_data, embedding):
    #     serialized_embedding = MovieRepository._serialize_embedding(embedding)

    #     movie = db.query(Movie).filter(Movie.id == movie_data.id).first()

    #     if movie:
    #         movie.title = movie_data.title
    #         movie.plot = movie_data.plot
    #         movie.genre = movie_data.genre
    #         movie.embedding = serialized_embedding
    #     else:
    #         movie = Movie(
    #             id=movie_data.id,
    #             title=movie_data.title,
    #             plot=movie_data.plot,
    #             genre=movie_data.genre,
    #             embedding=serialized_embedding
    #         )
    #         db.add(movie)

    #     db.commit()
    #     db.refresh(movie)

    #     return movie

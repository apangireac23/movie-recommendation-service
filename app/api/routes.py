from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import RecommendRequest, RecommendResponse, MovieIngestRequest, UserEventRequest
from app.services.recommender import get_recommendations
from app.services.movie_service import ingest_movie
from app.core.database import SessionLocal
from app.services.event_service import log_user_event

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/v1/movies")
def add_movie(req: MovieIngestRequest, db: Session = Depends(get_db)):

    movie = ingest_movie(db, req)

    return {
        "status": "stored",
        "movie_id": movie.id
    }


# @router.post("/v1/recommend", response_model=RecommendResponse)
# def recommend(req: RecommendRequest):

#     movies = get_recommendations(req.user_id)

#     return RecommendResponse(recommendations=movies)

@router.post("/recommendations", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)):

    movies = get_recommendations(req.user_id, db)

    return RecommendResponse(recommendations=movies)

@router.post("/v1/events")
def record_event(req: UserEventRequest, db: Session = Depends(get_db)):

    event = log_user_event(db, req)

    return {"status": "logged", "event_id": event.id}

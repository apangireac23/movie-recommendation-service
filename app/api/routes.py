from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import MovieIngestRequest, RecommendRequest, RecommendResponse, UserEventRequest
from app.services.event_service import log_user_event
from app.services.recommender import get_recommendations

router = APIRouter()


@router.post("/v1/movies")
def add_movie(req: MovieIngestRequest):
    raise HTTPException(
        status_code=501,
        detail=(
            "Movie ingestion is disabled in the stateless runtime. "
            "Precompute embeddings and rebuild index.faiss offline."
        ),
    )


@router.post("/v1/recommend", response_model=RecommendResponse)
@router.post("/recommendations", response_model=RecommendResponse)
def recommend(req: RecommendRequest, request: Request):
    runtime_store = request.app.state.runtime_store
    movies = get_recommendations(req, runtime_store)
    return RecommendResponse(recommendations=movies)


@router.post("/v1/events")
def record_event(req: UserEventRequest):
    event = log_user_event(req)
    return {"status": "logged", "event_id": event["id"]}

from fastapi import APIRouter

from app.api.schemas import EventsRecommendationRequest, RecommendResponse
from app.services.event_based_recommender import get_recommendations_from_events

router = APIRouter()

@router.post("/v1/recommendations/from-events", response_model=RecommendResponse)
def recommend_from_events(req: EventsRecommendationRequest):
    """Recommend from caller-provided events without external lookups."""

    movies = get_recommendations_from_events(req.events, req.limit)

    return RecommendResponse(recommendations=movies)

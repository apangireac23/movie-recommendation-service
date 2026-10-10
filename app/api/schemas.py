from typing import List, Literal

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    user_id: str


class RecommendResponse(BaseModel):
    recommendations: List[str]

class MovieIngestRequest(BaseModel):
    id: str
    title: str
    plot: str | None = None
    genre: str | None = None

class UserEventRequest(BaseModel):
    user_id: str
    movie_id: str
    event_type: str


class RecommendationEvent(BaseModel):
    """A user interaction supplied by the calling application."""

    movie_id: str
    event_type: Literal["watch", "like", "skip"]


class EventsRecommendationRequest(BaseModel):
    """Database-free recommendation input.

    The caller owns user history and sends the relevant events with each
    request, so this service does not need to persist users or their events.
    """

    events: List[RecommendationEvent]
    limit: int = Field(default=10, ge=1, le=50)

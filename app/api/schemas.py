from typing import Literal

from pydantic import BaseModel, Field


class RecommendResponse(BaseModel):
    recommendations: list[str]


class RecommendationEvent(BaseModel):
    """A user interaction supplied by the calling application."""

    movie_id: str
    event_type: Literal["watch", "like", "skip"]


class EventsRecommendationRequest(BaseModel):
    """Database-free recommendation input.

    The caller owns user history and sends the relevant events with each
    request, so this service does not need to persist users or their events.
    """

    events: list[RecommendationEvent]
    limit: int = Field(default=10, ge=1, le=50)

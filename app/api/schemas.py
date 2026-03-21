from typing import List

from pydantic import BaseModel, Field


class UserInteraction(BaseModel):
    movie_id: str
    event_type: str


class RecommendRequest(BaseModel):
    user_id: str | None = None
    movie_id: str | None = None
    seed_movie_ids: List[str] = Field(default_factory=list)
    interactions: List[UserInteraction] = Field(default_factory=list)


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

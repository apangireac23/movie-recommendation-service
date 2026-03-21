from pydantic import BaseModel
from typing import List


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
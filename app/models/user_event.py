from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from app.core.database import Base


class UserEvent(Base):

    __tablename__ = "user_events"

    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    movie_id = Column(String, index=True)
    event_type = Column(String)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
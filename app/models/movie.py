from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from app.core.database import Base


class Movie(Base):
    __tablename__ = "movies"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    plot = Column(Text)
    genre = Column(String)
    embedding = Column(JSONB)   # ✅ ADD THIS
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
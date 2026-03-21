import uuid
from sqlalchemy import func
from app.models.user_event import UserEvent


class EventRepository:

    @staticmethod
    def log_event(db, event_data):

        event = UserEvent(
            id=str(uuid.uuid4()),
            user_id=event_data.user_id,
            movie_id=event_data.movie_id,
            event_type=event_data.event_type
        )

        db.add(event)
        db.commit()

        return event


    @staticmethod
    def get_user_events(db, user_id):

        return db.query(UserEvent).filter(
            UserEvent.user_id == user_id
        ).all()
    

    @staticmethod
    def get_popular_movies(db, limit):

        results = (
            db.query(UserEvent.movie_id, func.count(UserEvent.id).label("cnt"))
            .group_by(UserEvent.movie_id)
            .order_by(func.count(UserEvent.id).desc())
            .limit(limit)
            .all()
        )

        return [r.movie_id for r in results]
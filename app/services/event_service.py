from app.repositories.event_repository import EventRepository


def log_user_event(db, event_data):

    event = EventRepository.log_event(db, event_data)

    return event
import uuid


def log_user_event(event_data):
    event = {
        "id": str(uuid.uuid4()),
        "user_id": event_data.user_id,
        "movie_id": event_data.movie_id,
        "event_type": event_data.event_type,
    }

    print(f"[EVENT] {event}")

    return event

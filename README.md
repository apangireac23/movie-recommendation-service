# Movie Recommendation Service

A stateless FastAPI service with one recommendation endpoint. It receives the
caller-owned interaction history in every request and queries a read-only
FAISS movie-index artifact loaded when the process starts. It does not connect
to PostgreSQL and does not persist users or events.

## Run locally

The service requires a matching artifact pair in `app/data/`:

- `movie_index.bin` — FAISS inner-product index
- `movie_index_map.json` — movie ids in FAISS-vector order

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

`POST /v1/recommendations/from-events`

```json
{
  "events": [
    {"movie_id": "tmdb_27205", "event_type": "like"},
    {"movie_id": "tmdb_862", "event_type": "skip"}
  ],
  "limit": 10
}
```

The response contains distinct movie ids that are absent from the submitted
events. Unknown movie ids are ignored. `watch`, `like`, and `skip` have
positive, stronger-positive, and negative weights respectively.

```json
{"recommendations": ["tmdb_...", "tmdb_..."]}
```

`GET /health` returns `{"status":"ok"}` for deployment probes. If artifacts
are missing or inconsistent, the recommendation endpoint returns HTTP 503.

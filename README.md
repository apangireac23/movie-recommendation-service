# Movie Recommendation Service

A stateless FastAPI service with one recommendation endpoint. It receives the
caller-owned interaction history in every request and queries a read-only
FAISS movie-index artifact loaded when the process starts. It does not connect
to PostgreSQL and does not persist users or events.

## Run locally

The service loads one complete artifact release. By default it uses
`artifacts/v1/`; configure another release with `ARTIFACT_DIR`.

- `movie_index.bin` — FAISS inner-product index
- `movie_index_map.json` — movie ids in FAISS-vector order
- `manifest.json` — version, counts, and integrity hashes

```bash
pip install -r requirements.txt
$env:ARTIFACT_DIR = "artifacts/v1"
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

`GET /health` reports the loaded artifact version and movie count. It and the
recommendation endpoint return HTTP 503 if the configured release is missing
or inconsistent.

## Build a catalogue artifact

`catalogue/movies.csv` is the manually maintained source catalogue. The API
does not read it. After updating that file, build a new artifact version:

```bash
pip install -r requirements-offline.txt
python scripts/build_artifacts.py --version v1
```

The command writes `artifacts/v1/` with a FAISS index, movie-id map, and a
manifest that records the source hash, embedding model, dimensions, and movie
count. By default it only uses a cached embedding model. Pass
`--allow-download` only when intentionally allowing the builder to download it.

Validate the CSV before building. The command fails for missing required
columns, duplicate headers, blank or duplicate ids, and when more than 1% of
rows lack a title or overview:

```bash
python scripts/build_artifacts.py --validate-only
```

## Test and evaluate retrieval

Run automated correctness tests:

```bash
python -m unittest discover -s tests -v
```

Run the hand-curated retrieval evaluation against the selected artifact release:

```bash
python scripts/evaluate_recommendations.py --min-mean-recall 0.5
```

The evaluation cases are a small starting baseline. Add human-reviewed relevant
movie ids before using its score to approve a ranking change.

## Run in a container

The image contains only the API and its runtime dependencies. Mount one
artifact release read-only when starting it; the CSV catalogue and offline
builder are not included.

```powershell
docker build --tag movie-recommendation-service:local .

$artifactPath = (Resolve-Path .\artifacts\v1).Path
docker run --rm --publish 8000:8000 `
  --mount "type=bind,source=$artifactPath,target=/artifacts/v1,readonly" `
  --env ARTIFACT_DIR=/artifacts/v1 `
  movie-recommendation-service:local
```

Verify the running container with `http://localhost:8000/health`. To use a new
catalogue release, mount `artifacts/v2` and set `ARTIFACT_DIR=/artifacts/v2`,
then start a new container.

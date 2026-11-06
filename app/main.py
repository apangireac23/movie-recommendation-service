import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.runtime_store import faiss_index
from app.ml.faiss_index import ArtifactNotReadyError

logging.basicConfig(level=logging.INFO)


app = FastAPI(
    title="Movie Recommendation Service",
    version="1.0",
)

app.include_router(router)


@app.get("/health")
def health():
    if not faiss_index.is_ready:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "detail": faiss_index.unavailable_reason},
        )
    return {
        "status": "ok",
        "artifact_version": faiss_index.artifact_version,
        "movie_count": faiss_index.movie_count,
    }


@app.exception_handler(ArtifactNotReadyError)
def artifact_not_ready_handler(request: Request, exc: ArtifactNotReadyError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )

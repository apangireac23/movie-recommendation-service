import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.ml.faiss_index import ArtifactNotReadyError

logging.basicConfig(level=logging.INFO)


app = FastAPI(
    title="Movie Recommendation Service",
    version="1.0",
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(ArtifactNotReadyError)
def artifact_not_ready_handler(request: Request, exc: ArtifactNotReadyError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )

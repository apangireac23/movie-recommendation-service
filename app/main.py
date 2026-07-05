import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.database import Base, engine
from app.core.runtime_store import faiss_index
from app.core.startup import rebuild_faiss_from_db
from app.models import movie
from app.services.recommender import FaissNotReadyError

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Populate from Postgres so a fresh deploy (empty app/data/) can
    # still serve real recommendations.
    rebuild_faiss_from_db(faiss_index)
    yield


app = FastAPI(
    title="Movie Recommendation Service",
    version="1.1",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(FaissNotReadyError)
def faiss_not_ready_handler(request: Request, exc: FaissNotReadyError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )

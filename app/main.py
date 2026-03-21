from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.routes import router
from app.core.runtime_store import RuntimeStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.runtime_store = RuntimeStore.load()
    yield


app = FastAPI(
    title="Movie Recommendation Service",
    version="1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health(request: Request):
    runtime_store = request.app.state.runtime_store
    return {
        "status": "ok",
        "index_size": runtime_store.index.ntotal,
    }

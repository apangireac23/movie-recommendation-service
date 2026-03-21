from fastapi import FastAPI
from app.api.routes import router
from app.core.database import engine, Base
from app.models import movie

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Movie Recommendation Service",
    version="1.0"
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
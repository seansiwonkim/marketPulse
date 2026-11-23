import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.articles import router as articles_router
from app.api.routes.sentiment import router as sentiment_router
from app.api.routes.status import router as status_router
from app.db.database import test_connection


app = FastAPI(title="marketPulse")

app.add_middleware(
    CORSMiddleware,
    # Comma-separated list of allowed frontend origins; set CORS_ORIGINS in production.
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET"],
)

# Tables are created and changed by Alembic migrations (`alembic upgrade head`), not here.

app.include_router(articles_router)
app.include_router(sentiment_router)
app.include_router(status_router)

@app.get("/")
async def root():
    return {"message": "Welcome to marketPulse API!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
def database_health():
    try:
        result = test_connection()
        return {
            "status": "connected",
            "database": "PostgreSQL",
            "test_query": result
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
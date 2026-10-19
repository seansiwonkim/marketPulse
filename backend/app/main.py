from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import Base, engine
from app.models.article import Article

from app.db.database import engine, test_connection
from app.api.routes.articles import router as articles_router
from app.models.sentiment import SentimentScore
from app.api.routes.sentiment import router as sentiment_router



app = FastAPI(title="marketPulse")

Base.metadata.create_all(bind=engine)  # Create tables if they don't exist

app.include_router(articles_router)
app.include_router(sentiment_router)

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
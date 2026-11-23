
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.article import Article
from app.models.sentiment import SentimentScore

router = APIRouter(prefix="/api/v1/stocks")

@router.get("/{ticker}/sentiment/daily")
def get_daily_sentiment(
    ticker: str,
    model: str = "ProsusAI/finbert",
    db: Session = Depends(get_db),
):
    day = func.date(Article.published_at)

    rows = db.execute(
        select(
            day.label("day"),
            func.avg(SentimentScore.score).label("avg_score"),
            func.count().label("article_count"),
        )
        .join(SentimentScore, SentimentScore.article_id == Article.id)
        .where(
            Article.ticker == ticker.upper(),
            SentimentScore.model_name == model,
        )
        .group_by(day)
        .order_by(day)
    ).all()

    return [
        {
            "date": r.day,
            "avg_score": round(r.avg_score, 3),
            "article_count": r.article_count,
        }
        for r in rows
    ]

@router.get("/{ticker}/sentiment")
def get_sentiment(
    ticker: str,
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Article, SentimentScore)
        .join(
            SentimentScore,
            Article.id == SentimentScore.article_id,
        )
        .where(Article.ticker == ticker.upper())
        .order_by(Article.published_at.desc())
        .limit(100)
    ).all()

    return [
        {
            "article_id": article.id,
            "title": article.title,
            "model": sentiment.model_name,
            "label": sentiment.label,
            "score": sentiment.score,
        }
        for article, sentiment in rows
    ]

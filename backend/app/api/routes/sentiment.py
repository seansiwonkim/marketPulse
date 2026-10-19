
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.article import Article
from app.models.sentiment import SentimentScore

router = APIRouter(prefix="/api/v1/stocks")


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

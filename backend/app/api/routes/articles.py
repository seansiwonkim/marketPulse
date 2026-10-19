from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.article import Article
from app.schemas.article import ArticleResponse

router = APIRouter(prefix="/api/v1/stocks")


@router.get(
    "/{ticker}/articles",
    response_model=list[ArticleResponse]
)
def get_articles(
    ticker: str,
    db: Session = Depends(get_db),
):
    statement = (
        select(Article)
        .where(Article.ticker == ticker.upper())
        .order_by(Article.published_at.desc())
        .limit(50)
    )

    return db.scalars(statement).all()
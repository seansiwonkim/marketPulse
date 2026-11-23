
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.services.news_service import NewsArticle


def save_articles(
    db: Session,
    articles: list[NewsArticle],
) -> int:

    inserted = 0

    for item in articles:
        url = str(item.url)

        existing = db.scalar(
            select(Article).where(Article.url == url)
        )

        if existing:
            continue

        article = Article(
            ticker=item.ticker,
            title=item.title,
            source=item.source,
            url=url,
            published_at=item.published_at,
        )

        db.add(article)
        db.flush()
        inserted += 1

    db.commit()

    return inserted

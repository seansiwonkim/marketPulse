from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select, tuple_
from sqlalchemy.orm import Session, aliased

from app.db.database import get_db
from app.models.article import Article
from app.models.sentiment import SentimentScore
from app.schemas.article import ArticlePage, ArticleWithSentiment, ModelResult

router = APIRouter(prefix="/api/v1")

FINBERT = "ProsusAI/finbert"
VADER = "vader"


def to_result(row: SentimentScore | None) -> ModelResult | None:
    if row is None:
        return None
    return ModelResult(model_name=row.model_name, label=row.label, score=row.score)


def parse_cursor(cursor: str) -> tuple[datetime, int]:
    # A cursor is "<published_at>|<id>": the last article of the previous page.
    ts, _, article_id = cursor.rpartition("|")
    try:
        return datetime.fromisoformat(ts), int(article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid cursor")


def fetch_page(
    db: Session,
    ticker: str | None,
    start: date | None,
    end: date | None,
    limit: int,
    cursor: str | None,
) -> ArticlePage:
    # Join the scores table twice, once per model. "outer" = left join:
    # keep the article even when that model has no row for it yet.
    # (article_id, model_name) is unique, so each article still appears once.
    finbert = aliased(SentimentScore)
    vader = aliased(SentimentScore)

    statement = (
        select(Article, finbert, vader)
        .outerjoin(
            finbert,
            and_(finbert.article_id == Article.id, finbert.model_name == FINBERT),
        )
        .outerjoin(
            vader,
            and_(vader.article_id == Article.id, vader.model_name == VADER),
        )
        # Newest first. id breaks ties, so the order is always the same.
        .order_by(Article.published_at.desc(), Article.id.desc())
        .limit(limit + 1)  # one extra row tells us whether another page exists
    )

    if ticker:
        statement = statement.where(Article.ticker == ticker.upper())
    if start:  # dates are whole UTC days, both ends inclusive
        statement = statement.where(
            Article.published_at >= datetime.combine(start, time.min, timezone.utc)
        )
    if end:
        statement = statement.where(
            Article.published_at
            < datetime.combine(end + timedelta(days=1), time.min, timezone.utc)
        )
    if cursor:
        # "Strictly older than the last article I saw", with id as the tie-breaker.
        ts, last_id = parse_cursor(cursor)
        statement = statement.where(
            tuple_(Article.published_at, Article.id) < tuple_(ts, last_id)
        )

    rows = db.execute(statement).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [
        ArticleWithSentiment(
            id=a.id,
            ticker=a.ticker,
            title=a.title,
            source=a.source,
            url=a.url,
            published_at=a.published_at,
            finbert=to_result(f),
            vader=to_result(v),
        )
        for a, f, v in rows
    ]
    last = rows[-1][0] if has_more else None
    return ArticlePage(
        items=items,
        next_cursor=f"{last.published_at.isoformat()}|{last.id}" if last else None,
    )


@router.get("/articles", response_model=ArticlePage)
def list_articles(
    ticker: str | None = None,  # leave out for every ticker
    start: date | None = None,
    end: date | None = None,
    limit: int = Query(24, ge=1, le=100),
    cursor: str | None = None,
    db: Session = Depends(get_db),
):
    return fetch_page(db, ticker, start, end, limit, cursor)


@router.get("/stocks/{ticker}/articles", response_model=ArticlePage)
def get_articles(
    ticker: str,
    start: date | None = None,
    end: date | None = None,
    limit: int = Query(24, ge=1, le=100),
    cursor: str | None = None,
    db: Session = Depends(get_db),
):
    return fetch_page(db, ticker, start, end, limit, cursor)

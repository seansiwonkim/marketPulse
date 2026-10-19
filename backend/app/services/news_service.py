
import os
from datetime import date, datetime, timezone
from app.schemas.article import ArticleCreate

import httpx
from pydantic import BaseModel, HttpUrl


class NewsArticle(BaseModel):
    ticker: str
    title: str
    source: str
    url: HttpUrl
    published_at: datetime


async def fetch_news(
    ticker: str,
    start_date: date,
    end_date: date,
) -> list[NewsArticle]:

    api_key = os.environ["FINNHUB_API_KEY"]

    url = "https://finnhub.io/api/v1/company-news"

    params = {
        "symbol": ticker,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "token": api_key,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    articles = []

    for item in data:
        if not item.get("headline") or not item.get("url"):
            continue

        article = ArticleCreate(
            ticker=ticker.upper(),
            title=item["headline"],
            source=item.get("source") or "Unknown",
            url=item["url"],
            published_at=datetime.fromtimestamp(
                item["datetime"],
                tz=timezone.utc,
            ),
        )

        articles.append(article)

    return articles

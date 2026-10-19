
import asyncio
from datetime import date, timedelta

from app.db.database import SessionLocal
from app.services.news_service import fetch_news
from app.services.article_service import save_articles


async def main():
    today = date.today()
    start = today - timedelta(days=7)

    tickers = ["NVDA", "AAPL", "TSLA"]

    for ticker in tickers:
        try:
            articles = await fetch_news(
                ticker,
                start,
                today,
            )

            with SessionLocal() as db:
                count = save_articles(db, articles)

            print(
                f"{ticker}: fetched {len(articles)}, "
                f"inserted {count}"
            )

        except Exception as exc:
            print(f"{ticker}: ingestion failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())

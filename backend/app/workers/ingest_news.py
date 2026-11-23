
import asyncio
from datetime import date, timedelta

from app.db.database import SessionLocal
from app.services.news_service import fetch_news
from app.services.article_service import save_articles
from app.services.pipeline_service import record_run


async def main() -> bool:
    """Fetch and save news. Returns True only if every ticker succeeded."""
    today = date.today()
    start = today - timedelta(days=7)

    tickers = ["NVDA", "AAPL", "TSLA"]
    inserted = 0
    failed = False

    for ticker in tickers:
        try:
            articles = await fetch_news(
                ticker,
                start,
                today,
            )

            with SessionLocal() as db:
                count = save_articles(db, articles)

            inserted += count
            print(
                f"{ticker}: fetched {len(articles)}, "
                f"inserted {count}"
            )

        except Exception as exc:
            failed = True
            print(f"{ticker}: ingestion failed: {exc}")

    if not failed:  # "News last fetched" only moves on a fully successful run
        with SessionLocal() as db:
            record_run(db, "ingest", inserted)
    return not failed


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(main()) else 1)

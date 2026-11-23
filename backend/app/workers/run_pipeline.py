"""The whole daily pipeline: fetch new articles, then score everything unscored.

    docker compose exec api python -m app.workers.run_pipeline
"""

import asyncio

from app.workers import analyze_sentiment, ingest_news


def main() -> int:
    fetched_ok = asyncio.run(ingest_news.main())
    # Score even if a fetch failed: articles already saved still need their scores.
    analyze_sentiment.run()
    return 0 if fetched_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

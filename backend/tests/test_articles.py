from datetime import datetime


from app.api.routes.articles import FINBERT, VADER
from app.models.article import Article
from app.models.sentiment import SentimentScore

T = datetime(2026, 11, 20, 12, 0)


def add_article(db, n, published_at=T, ticker="NVDA"):
    a = Article(
        id=n, ticker=ticker, title=f"headline {n}", source="Test",
        url=f"https://example.com/{n}", published_at=published_at,
    )
    db.add(a)
    db.commit()
    return a


def add_score(db, article_id, model, label, score):
    db.add(SentimentScore(
        article_id=article_id, model_name=model, label=label, score=score,
        positive=0.0, negative=0.0, neutral=0.0,
    ))
    db.commit()


def test_scored_partly_scored_and_unscored(client, db):
    add_article(db, 1)  # both models, and they disagree
    add_score(db, 1, FINBERT, "negative", -0.7)
    add_score(db, 1, VADER, "positive", 0.4)
    add_article(db, 2)  # FinBERT only, and a score of exactly 0
    add_score(db, 2, FINBERT, "neutral", 0.0)
    add_article(db, 3)  # not analyzed yet

    rows = {r["id"]: r for r in client.get("/api/v1/stocks/NVDA/articles").json()["items"]}

    assert len(rows) == 3  # nothing duplicated, nothing dropped
    assert rows[1]["finbert"]["label"] == "negative"
    assert rows[1]["vader"]["label"] == "positive"
    assert rows[2]["finbert"]["score"] == 0.0  # 0 is a real result...
    assert rows[2]["vader"] is None            # ...None means "no result"
    assert rows[3]["finbert"] is None and rows[3]["vader"] is None


def test_same_timestamp_has_stable_order(client, db):
    for n in (1, 2, 3):
        add_article(db, n)  # identical published_at
    ids = [r["id"] for r in client.get("/api/v1/stocks/NVDA/articles").json()["items"]]
    assert ids == [3, 2, 1]


def test_no_matching_articles(client, db):
    add_article(db, 1, ticker="AAPL")
    assert client.get("/api/v1/stocks/NVDA/articles").json() == {"items": [], "next_cursor": None}


def walk_pages(client, **params):
    """Follow next_cursor until the end; return the ids in the order received."""
    ids, cursor = [], None
    while True:
        page = client.get(
            "/api/v1/articles", params={**params, "cursor": cursor} if cursor else params
        ).json()
        ids += [a["id"] for a in page["items"]]
        cursor = page["next_cursor"]
        if cursor is None:
            return ids


def test_paging_has_no_duplicates_or_gaps_even_with_equal_timestamps(client, db):
    for n in range(1, 6):
        add_article(db, n)  # five articles, identical published_at
    add_article(db, 6, published_at=datetime(2026, 11, 21))  # one newer
    add_article(db, 7, published_at=datetime(2026, 11, 19))  # one older

    assert walk_pages(client, limit=2) == [6, 5, 4, 3, 2, 1, 7]


def test_last_page_has_no_cursor(client, db):
    add_article(db, 1)
    page = client.get("/api/v1/articles", params={"limit": 5}).json()
    assert len(page["items"]) == 1 and page["next_cursor"] is None


def test_all_tickers_and_single_ticker(client, db):
    add_article(db, 1, ticker="NVDA")
    add_article(db, 2, ticker="AAPL")
    assert sorted(walk_pages(client)) == [1, 2]
    assert walk_pages(client, ticker="aapl") == [2]


def test_date_range_is_inclusive_of_both_days(client, db):
    add_article(db, 1, published_at=datetime(2026, 11, 18, 23, 59))  # before
    add_article(db, 2, published_at=datetime(2026, 11, 19, 0, 0))    # first day
    add_article(db, 3, published_at=datetime(2026, 11, 20, 23, 59))  # last day
    add_article(db, 4, published_at=datetime(2026, 11, 21, 0, 0))    # after
    assert walk_pages(client, start="2026-11-19", end="2026-11-20") == [3, 2]


def test_bad_cursor_is_rejected(client):
    assert client.get("/api/v1/articles", params={"cursor": "nonsense"}).status_code == 400

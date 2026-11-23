from app.services.pipeline_service import last_success, record_run


def test_status_is_null_before_any_run(client):
    assert client.get("/api/v1/status").json() == {
        "news_last_fetched": None,
        "sentiment_last_scored": None,
    }


def test_status_reports_each_step_separately(client, db):
    record_run(db, "ingest", 12)  # only ingest has succeeded so far
    body = client.get("/api/v1/status").json()
    assert body["news_last_fetched"] is not None
    assert body["sentiment_last_scored"] is None

    record_run(db, "score", 12)
    assert client.get("/api/v1/status").json()["sentiment_last_scored"] is not None


def test_last_success_is_the_newest_run(db):
    record_run(db, "ingest", 1)
    record_run(db, "ingest", 2)
    assert last_success(db, "ingest") is not None
    assert last_success(db, "score") is None

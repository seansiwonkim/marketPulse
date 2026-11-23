
from sqlalchemy import exists, select

from app.db.database import SessionLocal
from app.models.article import Article
from app.models.sentiment import SentimentScore
from app.services.pipeline_service import record_run
from app.services.sentiment_service import (
    analyze_finbert,
    analyze_vader,
)

# model_name stored in the DB -> function that produces a prediction
MODELS = {
    "vader": analyze_vader,
    "ProsusAI/finbert": analyze_finbert,
}

COMMIT_EVERY = 50


def run():
    scored = 0
    with SessionLocal() as db:
        for model_name, analyze in MODELS.items():
            # Articles that have NO score row yet for this model.
            # Same idea as the SQL: WHERE NOT EXISTS (...)
            unscored = select(Article).where(
                ~exists().where(
                    SentimentScore.article_id == Article.id,
                    SentimentScore.model_name == model_name,
                )
            )
            articles = db.scalars(unscored).all()
            print(f"{model_name}: {len(articles)} articles to score")

            for i, article in enumerate(articles, start=1):
                prediction = analyze(article.title)
                scored += 1

                db.add(
                    SentimentScore(
                        article_id=article.id,
                        model_name=model_name,
                        label=prediction.label,
                        score=prediction.score,
                        positive=prediction.positive,
                        negative=prediction.negative,
                        neutral=prediction.neutral,
                    )
                )

                if i % COMMIT_EVERY == 0:
                    db.commit()
                    print(f"{model_name}: {i}/{len(articles)}")

            db.commit()  # flush the last partial batch

        # Reached only if nothing crashed above, so this time means "scoring succeeded".
        record_run(db, "score", scored)


if __name__ == "__main__":
    run()

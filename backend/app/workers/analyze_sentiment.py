
from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.article import Article
from app.models.sentiment import SentimentScore
from app.services.sentiment_service import (
    analyze_finbert,
    analyze_vader,
)


def run():
    with SessionLocal() as db:
        articles = db.scalars(
            select(Article).order_by(Article.id).limit(100)
        ).all()

        for article in articles:
            existing_models = set(
                db.scalars(
                    select(SentimentScore.model_name).where(
                        SentimentScore.article_id == article.id
                    )
                ).all()
            )

            for analyze in (analyze_finbert, analyze_vader):
                model_name = (
                    "ProsusAI/finbert"
                    if analyze == analyze_finbert
                    else "vader"
                )

                if model_name in existing_models:
                    continue

                prediction = analyze(article.title)

                db.add(
                    SentimentScore(
                        article_id=article.id,
                        model_name=prediction.model_name,
                        label=prediction.label,
                        score=prediction.score,
                        positive=prediction.positive,
                        negative=prediction.negative,
                        neutral=prediction.neutral,
                    )
                )

                db.commit()

                print(
                    article.ticker,
                    prediction.model_name,
                    prediction.label,
                    round(prediction.score, 3),
                )


if __name__ == "__main__":
    run()

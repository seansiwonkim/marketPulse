
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "model_name",
            name="uq_article_sentiment_model",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id"),
        nullable=False,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    positive: Mapped[float] = mapped_column(Float)
    negative: Mapped[float] = mapped_column(Float)
    neutral: Mapped[float] = mapped_column(Float)

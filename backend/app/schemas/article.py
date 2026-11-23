
# backend/app/schemas/article.py

from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl, Field


class ArticleBase(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    title: str = Field(min_length=1)
    source: str = Field(min_length=1)
    url: HttpUrl
    published_at: datetime


class ArticleCreate(ArticleBase):
    """Validated data used to create an article."""
    pass


class ArticleResponse(ArticleBase):
    """Article returned by our API."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class ModelResult(BaseModel):
    """One model's verdict on one article.

    The score scales differ, so don't compare numbers across models:
      - FinBERT: positive probability minus negative probability (-1..1)
      - VADER:   its compound score (-1..1)
    """
    model_name: str
    label: str
    score: float  # 0.0 means a balanced score, NOT "missing" (missing is None below)


class ArticleWithSentiment(ArticleResponse):
    """An article plus each model's result. None = not analyzed yet."""
    finbert: ModelResult | None
    vader: ModelResult | None


class ArticlePage(BaseModel):
    """One batch of articles. Pass next_cursor back to get the following batch."""
    items: list[ArticleWithSentiment]
    next_cursor: str | None  # None = no more articles

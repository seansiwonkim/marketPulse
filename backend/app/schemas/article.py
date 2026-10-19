
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

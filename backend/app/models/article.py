
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    ticker: Mapped[str] = mapped_column(
        String(10),
        index=True
    )

    source: Mapped[str] = mapped_column(
        String(255)
    )

    url: Mapped[str] = mapped_column(
        Text,
        unique=True
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

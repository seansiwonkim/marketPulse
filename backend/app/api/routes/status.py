from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.pipeline_service import last_success

router = APIRouter(prefix="/api/v1")


class Status(BaseModel):
    news_last_fetched: datetime | None  # last successful ingest; None = never
    sentiment_last_scored: datetime | None  # last successful scoring run


@router.get("/status", response_model=Status)
def get_status(db: Session = Depends(get_db)):
    return Status(
        news_last_fetched=last_success(db, "ingest"),
        sentiment_last_scored=last_success(db, "score"),
    )

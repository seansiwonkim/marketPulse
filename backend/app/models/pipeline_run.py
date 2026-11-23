from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class PipelineRun(Base):
    """One row per SUCCESSFUL pipeline step ('ingest' or 'score'). Failures aren't recorded."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    step: Mapped[str] = mapped_column(String(20), index=True)
    finished_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    rows: Mapped[int] = mapped_column(Integer)  # articles inserted, or scores written

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.pipeline_run import PipelineRun


def record_run(db: Session, step: str, rows: int) -> None:
    db.add(PipelineRun(step=step, rows=rows))
    db.commit()


def last_success(db: Session, step: str):
    """When this step last succeeded, or None if it never has."""
    return db.scalar(
        select(func.max(PipelineRun.finished_at)).where(PipelineRun.step == step)
    )


from pydantic import BaseModel, Field


class SentimentPrediction(BaseModel):
    label: str
    positive: float = Field(ge=0, le=1)
    negative: float = Field(ge=0, le=1)
    neutral: float = Field(ge=0, le=1)
    score: float = Field(ge=-1, le=1)
    model_name: str


from email.mime import text
from functools import lru_cache

from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.schemas.sentiment import SentimentPrediction

@lru_cache(maxsize=1)
def get_finbert():
    return pipeline(
        task="text-classification",
        model="ProsusAI/finbert",
        top_k=None,
        device=-1,
    )


@lru_cache(maxsize=1)
def get_vader():
    return SentimentIntensityAnalyzer()


def analyze_finbert(text: str) -> SentimentPrediction:
    classifier = get_finbert()
    results = classifier(text, truncation=True)
    if results and isinstance(results[0], list):
        results = results[0]

    probabilities = {
        item["label"].lower(): item["score"]
        for item in results
    }

    positive = probabilities["positive"]
    negative = probabilities["negative"]
    neutral = probabilities["neutral"]

    label = max(probabilities, key=probabilities.get)

    return SentimentPrediction(
        label=label,
        positive=positive,
        negative=negative,
        neutral=neutral,
        score=positive - negative,
        model_name="ProsusAI/finbert",
    )


def analyze_vader(text: str) -> SentimentPrediction:
    scores = get_vader().polarity_scores(text)

    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return SentimentPrediction(
        label=label,
        positive=scores["pos"],
        negative=scores["neg"],
        neutral=scores["neu"],
        score=compound,
        model_name="vader",
    )

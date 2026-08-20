from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from config import settings
from models.models import (
    AnalyzeMultipleResponse,
    AnalyzeResponse,
    CacheInvalidationResponse,
    MultiTextRequest,
    SentimentClassesResponse,
    SentimentScores,
    SentimentStatistics,
    StatisticsResponse,
    TextRequest,
)
from services.cache_service import sentiment_cache
from services.sentiment_service import SentimentService

router = APIRouter(prefix='/v1')
sentiment_service = SentimentService(cache=sentiment_cache)

SENTIMENT_CLASSES = {
    'positive': 'Scores greater than 0.05',
    'neutral': 'Scores between -0.05 and 0.05',
    'negative': 'Scores less than -0.05',
}


@router.post(
    '/analyze',
    response_model=AnalyzeResponse,
    tags=['sentiment'],
    summary='Analyze the sentiment of a single text',
    description='Returns polarity scores (compound, pos, neu, neg) for the given text.',
)
def analyze(request: TextRequest) -> AnalyzeResponse:
    if not request.text:
        raise HTTPException(status_code=400, detail='No text provided')

    scores = sentiment_service.analyze_sentiment(request.text, request.language)
    return AnalyzeResponse(
        text=request.text,
        language=request.language,
        sentiment=SentimentScores(**scores),
    )


@router.post(
    '/analyze_multiple',
    response_model=AnalyzeMultipleResponse,
    tags=['sentiment'],
    summary='Analyze the sentiment of multiple texts',
    description='Returns polarity scores keyed by each input text.',
)
def analyze_multiple(request: MultiTextRequest) -> AnalyzeMultipleResponse:
    if not request.texts:
        raise HTTPException(status_code=400, detail='No texts provided')

    results = sentiment_service.analyze_multiple_sentiments(
        request.texts, request.language
    )
    return AnalyzeMultipleResponse(
        results={text: SentimentScores(**scores) for text, scores in results.items()}
    )


@router.get(
    '/sentiment_classes',
    response_model=SentimentClassesResponse,
    tags=['sentiment'],
    summary='List sentiment classification thresholds',
)
def sentiment_classes() -> SentimentClassesResponse:
    return SentimentClassesResponse(classes=SENTIMENT_CLASSES)


@router.post(
    '/analyze_statistics',
    response_model=StatisticsResponse,
    tags=['sentiment'],
    summary='Sentiment distribution statistics',
    description='Counts how many texts are classified as positive, neutral or negative.',
)
def analyze_statistics(request: MultiTextRequest) -> StatisticsResponse:
    if not request.texts:
        raise HTTPException(status_code=400, detail='No texts provided')

    statistics = sentiment_service.analyze_statistics(request.texts, request.language)
    return StatisticsResponse(statistics=SentimentStatistics(**statistics))


def _ensure_admin(x_admin_token: str | None) -> None:
    if settings.admin_token and x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail='Invalid admin token')


@router.delete(
    '/cache',
    response_model=CacheInvalidationResponse,
    tags=['admin'],
    summary='Invalidate the sentiment cache',
    description='Clears all cached sentiment scores. Requires the X-Admin-Token header when '
    'ADMIN_TOKEN is configured.',
)
def invalidate_cache(
    x_admin_token: Annotated[str | None, Header()] = None,
) -> CacheInvalidationResponse:
    _ensure_admin(x_admin_token)
    cleared = sentiment_cache.clear()
    return CacheInvalidationResponse(status='cache invalidated', cleared=cleared)

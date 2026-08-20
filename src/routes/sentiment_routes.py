import json
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from fastapi.responses import StreamingResponse

from config import settings
from models.models import (
    AnalyzeMultipleResponse,
    AnalyzeResponse,
    BatchAcceptedResponse,
    CacheInvalidationResponse,
    JobResultResponse,
    MultiTextRequest,
    SentimentClassesResponse,
    SentimentScores,
    SentimentStatistics,
    StatisticsResponse,
    TextRequest,
)
from services.cache_service import sentiment_cache
from services.job_store import JobStore, process_job
from services.sentiment_service import SentimentService

router = APIRouter(prefix='/v1')
sentiment_service = SentimentService(cache=sentiment_cache)
job_store = JobStore(maxsize=settings.job_store_maxsize)

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


@router.post(
    '/analyze_batch',
    response_model=BatchAcceptedResponse,
    status_code=202,
    tags=['batch'],
    summary='Submit a batch of texts for asynchronous analysis',
    description='Accepts a large batch and returns a job id immediately. Poll '
    '`/v1/results/{job_id}` until status is `completed` or `failed`.',
)
def submit_batch(
    request: MultiTextRequest, background_tasks: BackgroundTasks
) -> BatchAcceptedResponse:
    if not request.texts:
        raise HTTPException(status_code=400, detail='No texts provided')

    job = job_store.create(total=len(request.texts), language=request.language)
    background_tasks.add_task(
        process_job,
        job_store,
        sentiment_service,
        job.id,
        request.texts,
        request.language,
    )
    return BatchAcceptedResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        results_url=f'/v1/results/{job.id}',
    )


@router.get(
    '/results/{job_id}',
    response_model=JobResultResponse,
    tags=['batch'],
    summary='Get the result of an asynchronous batch job',
)
def get_results(job_id: str) -> JobResultResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail='Job not found')

    return JobResultResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        processed=job.processed,
        language=job.language,
        results={
            text: SentimentScores(**scores) for text, scores in job.results.items()
        }
        or None,
    )


@router.post(
    '/analyze_stream',
    tags=['stream'],
    summary='Stream sentiment analysis results via Server-Sent Events',
    description='Analyzes each text progressively and emits one `data` event per text, '
    'followed by a final `done` event.',
)
def analyze_stream(request: MultiTextRequest) -> StreamingResponse:
    if not request.texts:
        raise HTTPException(status_code=400, detail='No texts provided')

    def event_stream() -> Iterator[str]:
        for text in request.texts:
            scores = sentiment_service.analyze_sentiment(text, request.language)
            payload = {'text': text, 'sentiment': scores}
            yield f'data: {json.dumps(payload)}\n\n'
        yield 'event: done\ndata: {}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache'},
    )

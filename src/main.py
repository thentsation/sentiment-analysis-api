import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from config import settings
from middlewares.metrics import MetricsMiddleware
from middlewares.process_time import ProcessTimeMiddleware
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.request_context import RequestContextMiddleware
from middlewares.security_headers import SecurityHeadersMiddleware
from models.models import HealthResponse, RootResponse
from observability.logging import configure_logging
from observability.sentry import init_sentry
from routes import sentiment_routes
from routes.sentiment_routes import router

configure_logging(settings.log_level, settings.log_format)
init_sentry(settings.sentry_dsn, traces_sample_rate=settings.sentry_traces_sample_rate)

API_NAME = 'Sentiment Analysis API'

app = FastAPI(
    title=API_NAME,
    version=settings.version,
    description='Sentiment analysis API (VADER for English, LeIA for Portuguese) with async '
    'batch jobs, SSE streaming, caching and observability.',
)
app.include_router(router)

app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/', response_model=RootResponse, tags=['meta'], summary='API metadata')
def root() -> RootResponse:
    endpoints = sorted(
        route.path
        for route in sentiment_routes.router.routes
        if isinstance(route, APIRoute) and route.path.startswith('/v1')
    )
    return RootResponse(
        name=API_NAME,
        version=settings.version,
        docs='/docs',
        health='/health',
        metrics='/metrics',
        endpoints=endpoints,
    )


@app.get(
    '/health', response_model=HealthResponse, tags=['meta'], summary='Health check'
)
def health_check() -> HealthResponse:
    return HealthResponse(status='ok')


@app.get(
    '/metrics', tags=['meta'], summary='Prometheus metrics', response_class=Response
)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={'detail': 'Internal server error'})


def run() -> None:
    if settings.workers > 1:
        src_dir = str(Path(__file__).resolve().parent)
        os.environ['PYTHONPATH'] = os.pathsep.join(
            [src_dir, os.environ.get('PYTHONPATH', '')]
        ).rstrip(os.pathsep)
        uvicorn.run(
            'main:app',
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level,
            workers=settings.workers,
        )
    else:
        uvicorn.run(
            app, host=settings.host, port=settings.port, log_level=settings.log_level
        )


if __name__ == '__main__':
    run()

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from config import settings
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.security_headers import SecurityHeadersMiddleware
from models.models import HealthResponse, RootResponse
from routes import sentiment_routes
from routes.sentiment_routes import router

API_NAME = 'Sentiment Analysis API'

app = FastAPI(
    title=API_NAME,
    version=settings.version,
    description='Sentiment analysis API using NLTK VADER, with async batch jobs, SSE streaming and caching.',
)
app.include_router(router)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
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
        endpoints=endpoints,
    )


@app.get(
    '/health', response_model=HealthResponse, tags=['meta'], summary='Health check'
)
def health_check() -> HealthResponse:
    return HealthResponse(status='ok')


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={'detail': 'Internal server error'})


def run() -> None:
    uvicorn.run(
        app, host=settings.host, port=settings.port, log_level=settings.log_level
    )


if __name__ == '__main__':
    run()

from fastapi import FastAPI
from fastapi.testclient import TestClient

from middlewares.rate_limit import RateLimitMiddleware


def build_app(limit_per_minute: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit_per_minute=limit_per_minute)

    @app.get('/ping')
    def ping() -> dict[str, str]:
        return {'pong': 'ok'}

    return app


def test_rate_limit_allows_requests_under_limit():
    client = TestClient(build_app(limit_per_minute=5))

    responses = [client.get('/ping') for _ in range(5)]

    assert all(response.status_code == 200 for response in responses)


def test_rate_limit_returns_429_above_limit():
    client = TestClient(build_app(limit_per_minute=3))

    statuses = [client.get('/ping').status_code for _ in range(5)]

    assert statuses == [200, 200, 200, 429, 429]


def test_rate_limit_response_includes_retry_after():
    client = TestClient(build_app(limit_per_minute=1))
    client.get('/ping')

    response = client.get('/ping')

    assert response.status_code == 429
    assert response.headers['Retry-After'] == '60'
    assert response.json()['detail'] == 'Too many requests'

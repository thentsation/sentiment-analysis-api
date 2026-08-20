import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, limit_per_minute: int = 100) -> None:
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        self._requests: dict[tuple[str, int], int] = {}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        client = request.client.host if request.client else 'unknown'
        window = int(time.time() // 60)
        key = (client, window)

        count = self._requests.get(key, 0) + 1
        self._requests[key] = count

        if len(self._requests) > 10_000:
            self._requests = {k: v for k, v in self._requests.items() if k[1] >= window}

        if count > self.limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={'detail': 'Too many requests'},
                headers={'Retry-After': '60'},
            )

        return await call_next(request)

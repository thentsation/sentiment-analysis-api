import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from middlewares.rate_limit import RateLimitMiddleware
from middlewares.security_headers import SecurityHeadersMiddleware
from routes.sentiment_routes import router

app = FastAPI()
app.include_router(router)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={'detail': 'Internal server error'})


def run() -> None:
    uvicorn.run(
        app, host=settings.host, port=settings.port, log_level=settings.log_level
    )


if __name__ == '__main__':
    run()

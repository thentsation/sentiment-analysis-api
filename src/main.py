import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routes.sentiment_routes import router

app = FastAPI()
app.include_router(router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={'detail': 'Internal server error'})


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')

from fastapi import APIRouter, HTTPException
from models.models import TextRequest, MultiTextRequest
from services.sentiment_service import SentimentService

router = APIRouter()
sentiment_service = SentimentService()

@router.post('/analyze')
def analyze(request: TextRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail='No text provided')
    
    result = sentiment_service.analyze_sentiment(request.text)
    return {'text': request.text, 'sentiment': result}

@router.post('/analyze_multiple')
def analyze_multiple(request: MultiTextRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail='No texts provided')
    
    results = sentiment_service.analyze_multiple_sentiments(request.texts)
    return {'results': results}

@router.get('/sentiment_classes')
def sentiment_classes():
    classes = {
        'positive': 'Scores greater than 0.05',
        'neutral': 'Scores between -0.05 and 0.05',
        'negative': 'Scores less than -0.05'
    }
    return {'classes': classes}

@router.post('/analyze_statistics')
def analyze_statistics(request: MultiTextRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail='No texts provided')
    
    statistics = sentiment_service.analyze_statistics(request.texts)
    return {'statistics': statistics}
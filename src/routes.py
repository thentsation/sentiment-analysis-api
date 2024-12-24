from fastapi import APIRouter, HTTPException
from models import TextRequest, MultiTextRequest
from sentiment import analyze_sentiment

router = APIRouter()

@router.post('/analyze')
def analyze(request: TextRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail='No text provided')
    
    result = analyze_sentiment(request.text)
    return {'text': request.text, 'sentiment': result}

@router.post('/analyze_multiple')
def analyze_multiple(request: MultiTextRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail='No texts provided')
    
    results = {}
    for text in request.texts:
        results[text] = analyze_sentiment(text)
    
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
    
    total_sentiment = {'positive': 0, 'neutral': 0, 'negative': 0}
    for text in request.texts:
        score = analyze_sentiment(text)
        if score['compound'] > 0.05:
            total_sentiment['positive'] += 1
        elif score['compound'] < -0.05:
            total_sentiment['negative'] += 1
        else:
            total_sentiment['neutral'] += 1
    
    return {'statistics': total_sentiment}

from fastapi.testclient import TestClient

from main import app
from routes.sentiment_routes import sentiment_service

client = TestClient(app)


def test_analyze_success():
    response = client.post('/analyze', json={'text': 'I love this!'})

    assert response.status_code == 200
    body = response.json()
    assert body['text'] == 'I love this!'
    assert set(body['sentiment'].keys()) == {'compound', 'pos', 'neu', 'neg'}
    assert body['sentiment']['compound'] > 0


def test_analyze_empty_text_returns_400():
    response = client.post('/analyze', json={'text': ''})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No text provided'


def test_analyze_multiple_success():
    response = client.post('/analyze_multiple', json={'texts': ['I love this!', 'I hate this!']})

    assert response.status_code == 200
    body = response.json()
    assert set(body['results'].keys()) == {'I love this!', 'I hate this!'}


def test_analyze_multiple_empty_list_returns_400():
    response = client.post('/analyze_multiple', json={'texts': []})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No texts provided'


def test_sentiment_classes_success():
    response = client.get('/sentiment_classes')

    assert response.status_code == 200
    classes = response.json()['classes']
    assert set(classes.keys()) == {'positive', 'neutral', 'negative'}


def test_analyze_statistics_success():
    response = client.post('/analyze_statistics', json={'texts': ['I love this!', 'I hate this!']})

    assert response.status_code == 200
    statistics = response.json()['statistics']
    assert statistics == {'positive': 1, 'neutral': 0, 'negative': 1}


def test_analyze_statistics_empty_list_returns_400():
    response = client.post('/analyze_statistics', json={'texts': []})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No texts provided'


def test_analyze_internal_error_returns_500(monkeypatch):
    def unexpected_error(text):
        raise RuntimeError('boom')

    monkeypatch.setattr(sentiment_service, 'analyze_sentiment', unexpected_error)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post('/analyze', json={'text': 'I love this!'})

    assert response.status_code == 500
    assert response.json()['detail'] == 'Internal server error'

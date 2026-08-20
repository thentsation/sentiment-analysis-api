from fastapi.testclient import TestClient

from main import app
from routes.sentiment_routes import sentiment_service

client = TestClient(app)


def test_analyze_success():
    response = client.post('/v1/analyze', json={'text': 'I love this!'})

    assert response.status_code == 200
    body = response.json()
    assert body['text'] == 'I love this!'
    assert body['language'] == 'en'
    assert set(body['sentiment'].keys()) == {'compound', 'pos', 'neu', 'neg'}
    assert body['sentiment']['compound'] > 0


def test_analyze_portuguese_positive():
    response = client.post(
        '/v1/analyze', json={'text': 'Eu amo isso, é maravilhoso!', 'language': 'pt'}
    )

    assert response.status_code == 200
    assert response.json()['language'] == 'pt'
    assert response.json()['sentiment']['compound'] > 0


def test_analyze_portuguese_negative():
    response = client.post(
        '/v1/analyze', json={'text': 'Eu odeio isso, é terrível!', 'language': 'pt'}
    )

    assert response.status_code == 200
    assert response.json()['sentiment']['compound'] < 0


def test_analyze_invalid_language_returns_422():
    response = client.post('/v1/analyze', json={'text': 'bonjour', 'language': 'fr'})

    assert response.status_code == 422


def test_analyze_empty_text_returns_400():
    response = client.post('/v1/analyze', json={'text': ''})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No text provided'


def test_analyze_text_over_max_length_returns_422():
    response = client.post('/v1/analyze', json={'text': 'a' * 10_001})

    assert response.status_code == 422


def test_analyze_multiple_over_max_texts_returns_422():
    response = client.post('/v1/analyze_multiple', json={'texts': ['ok'] * 101})

    assert response.status_code == 422


def test_analyze_multiple_success():
    response = client.post(
        '/v1/analyze_multiple', json={'texts': ['I love this!', 'I hate this!']}
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body['results'].keys()) == {'I love this!', 'I hate this!'}


def test_analyze_multiple_empty_list_returns_400():
    response = client.post('/v1/analyze_multiple', json={'texts': []})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No texts provided'


def test_sentiment_classes_success():
    response = client.get('/v1/sentiment_classes')

    assert response.status_code == 200
    classes = response.json()['classes']
    assert set(classes.keys()) == {'positive', 'neutral', 'negative'}


def test_analyze_statistics_success():
    response = client.post(
        '/v1/analyze_statistics', json={'texts': ['I love this!', 'I hate this!']}
    )

    assert response.status_code == 200
    statistics = response.json()['statistics']
    assert statistics == {'positive': 1, 'neutral': 0, 'negative': 1}


def test_analyze_statistics_empty_list_returns_400():
    response = client.post('/v1/analyze_statistics', json={'texts': []})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No texts provided'


def test_analyze_internal_error_returns_500(monkeypatch):
    def unexpected_error(text, language='en'):
        raise RuntimeError('boom')

    monkeypatch.setattr(sentiment_service, 'analyze_sentiment', unexpected_error)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post('/v1/analyze', json={'text': 'I love this!'})

    assert response.status_code == 500
    assert response.json()['detail'] == 'Internal server error'


def test_delete_cache_without_token_by_default():
    response = client.delete('/v1/cache')

    assert response.status_code == 200
    assert response.json()['status'] == 'cache invalidated'
    assert response.json()['cleared'] >= 0


def test_delete_cache_with_invalid_token_returns_401(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, 'admin_token', 'secret')

    response = client.delete('/v1/cache')

    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid admin token'


def test_delete_cache_with_valid_token(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, 'admin_token', 'secret')
    client.post('/v1/analyze', json={'text': 'I love this!'})

    response = client.delete('/v1/cache', headers={'X-Admin-Token': 'secret'})

    assert response.status_code == 200
    assert response.json()['cleared'] >= 1

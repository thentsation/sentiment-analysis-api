import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_analyze_stream_returns_sse_events():
    response = client.post(
        '/v1/analyze_stream', json={'texts': ['I love this!', 'I hate this!']}
    )

    assert response.status_code == 200
    assert 'text/event-stream' in response.headers['content-type']
    assert response.headers['cache-control'] == 'no-cache'


def test_analyze_stream_emits_one_event_per_text_then_done():
    response = client.post(
        '/v1/analyze_stream', json={'texts': ['I love this!', 'I hate this!']}
    )

    events = [line for line in response.text.splitlines() if line.startswith('data: ')]
    assert len(events) == 3

    first = json.loads(events[0][len('data: ') :])
    assert first['text'] == 'I love this!'
    assert first['sentiment']['compound'] > 0

    second = json.loads(events[1][len('data: ') :])
    assert second['sentiment']['compound'] < 0

    assert json.loads(events[2][len('data: ') :]) == {}


def test_analyze_stream_done_event_has_event_name():
    response = client.post('/v1/analyze_stream', json={'texts': ['ok']})

    assert 'event: done' in response.text


def test_analyze_stream_empty_list_returns_400():
    response = client.post('/v1/analyze_stream', json={'texts': []})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No texts provided'


def test_analyze_stream_portuguese():
    response = client.post(
        '/v1/analyze_stream',
        json={'texts': ['Eu amo isso, é maravilhoso!'], 'language': 'pt'},
    )

    events = [line for line in response.text.splitlines() if line.startswith('data: ')]
    payload = json.loads(events[0][len('data: ') :])
    assert payload['sentiment']['compound'] > 0

from fastapi.testclient import TestClient

from main import app
from routes.sentiment_routes import sentiment_service
from services.job_store import JobStore

client = TestClient(app)


def test_submit_batch_returns_202_with_job_id():
    response = client.post(
        '/v1/analyze_batch', json={'texts': ['I love this!', 'I hate this!']}
    )

    assert response.status_code == 202
    body = response.json()
    assert body['job_id']
    assert body['status'] == 'pending'
    assert body['total'] == 2
    assert body['results_url'] == f'/v1/results/{body["job_id"]}'


def test_batch_completes_with_results():
    accepted = client.post(
        '/v1/analyze_batch', json={'texts': ['I love this!', 'I hate this!']}
    ).json()

    response = client.get(f'/v1/results/{accepted["job_id"]}')

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'completed'
    assert body['processed'] == 2
    assert body['results']['I love this!']['compound'] > 0
    assert body['results']['I hate this!']['compound'] < 0


def test_batch_portuguese():
    accepted = client.post(
        '/v1/analyze_batch',
        json={'texts': ['Eu amo isso, é maravilhoso!'], 'language': 'pt'},
    ).json()

    body = client.get(f'/v1/results/{accepted["job_id"]}').json()

    assert body['language'] == 'pt'
    assert body['status'] == 'completed'
    assert body['results']['Eu amo isso, é maravilhoso!']['compound'] > 0


def test_batch_empty_list_returns_400():
    response = client.post('/v1/analyze_batch', json={'texts': []})

    assert response.status_code == 400
    assert response.json()['detail'] == 'No texts provided'


def test_results_unknown_job_returns_404():
    response = client.get('/v1/results/does-not-exist')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Job not found'


def test_results_pending_job_returns_no_results():
    from routes.sentiment_routes import job_store

    job = job_store.create(total=5, language='en')

    response = client.get(f'/v1/results/{job.id}')

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'pending'
    assert body['processed'] == 0
    assert body['results'] is None


def test_batch_failure_marks_job_as_failed(monkeypatch):
    def unexpected_error(text, language='en'):
        raise RuntimeError('boom')

    monkeypatch.setattr(sentiment_service, 'analyze_sentiment', unexpected_error)

    accepted = client.post('/v1/analyze_batch', json={'texts': ['anything']}).json()
    body = client.get(f'/v1/results/{accepted["job_id"]}').json()

    assert body['status'] == 'failed'


def test_job_store_evicts_oldest_job():
    store = JobStore(maxsize=2)

    first = store.create(total=1, language='en')
    store.create(total=1, language='en')
    store.create(total=1, language='en')

    assert store.get(first.id) is None
    assert len({job.id for job in (store.create(total=1, language='en'),)}) == 1

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EXPECTED_PATHS = {
    '/': {'get'},
    '/health': {'get'},
    '/v1/analyze': {'post'},
    '/v1/analyze_multiple': {'post'},
    '/v1/analyze_statistics': {'post'},
    '/v1/analyze_batch': {'post'},
    '/v1/results/{job_id}': {'get'},
    '/v1/analyze_stream': {'post'},
    '/v1/sentiment_classes': {'get'},
    '/v1/cache': {'delete'},
}

EXPECTED_SCHEMAS = [
    'TextRequest',
    'MultiTextRequest',
    'SentimentScores',
    'AnalyzeResponse',
    'AnalyzeMultipleResponse',
    'SentimentClassesResponse',
    'StatisticsResponse',
]


def test_root_metadata():
    response = client.get('/')

    assert response.status_code == 200
    body = response.json()
    assert body['name'] == 'Sentiment Analysis API'
    assert body['version']
    assert body['docs'] == '/docs'
    assert body['health'] == '/health'
    assert '/v1/analyze' in body['endpoints']


def test_openapi_contract_paths_and_methods():
    spec = client.get('/openapi.json').json()

    assert spec['info']['title'] == 'Sentiment Analysis API'
    for path, methods in EXPECTED_PATHS.items():
        assert path in spec['paths'], f'missing path {path}'
        assert methods <= set(spec['paths'][path]), f'missing methods for {path}'


def test_openapi_contract_response_schemas():
    spec = client.get('/openapi.json').json()
    schemas = spec['components']['schemas']

    for name in EXPECTED_SCHEMAS:
        assert name in schemas, f'missing schema {name}'

    assert schemas['TextRequest']['properties']['text']['maxLength'] == 10_000


def test_openapi_contract_language_enum():
    spec = client.get('/openapi.json').json()
    language = spec['components']['schemas']['TextRequest']['properties']['language']

    assert language['enum'] == ['en', 'pt']
    assert language['default'] == 'en'


def test_metrics_endpoint_exposes_http_and_business_metrics():
    client.post('/v1/analyze', json={'text': 'I love this!'})

    response = client.get('/metrics')

    assert response.status_code == 200
    body = response.text
    assert 'http_requests_total' in body
    assert 'http_request_duration_seconds' in body
    assert 'sentiment_analysis_total' in body
    assert 'cache_hits_total' in body
    assert 'cache_misses_total' in body
    assert 'batch_jobs_total' in body


def test_metrics_uses_route_template_as_label():
    client.post('/v1/analyze', json={'text': 'I love this!'})
    client.post('/v1/analyze', json={'text': 'I hate this!'})

    response = client.get('/metrics')

    assert '/v1/analyze"' in response.text or '/v1/analyze ' in response.text


def test_request_id_header_is_generated():
    response = client.get('/health')

    assert response.status_code == 200
    assert response.headers.get('X-Request-ID')


def test_request_id_header_is_preserved_from_client():
    response = client.get('/health', headers={'X-Request-ID': 'my-custom-id'})

    assert response.headers['X-Request-ID'] == 'my-custom-id'


def test_process_time_header_is_present():
    response = client.get('/health')

    assert response.status_code == 200
    assert float(response.headers['X-Process-Time-Ms']) >= 0


def test_sentry_disabled_without_dsn():
    from observability.sentry import init_sentry

    assert init_sentry('') is False


def test_sentry_enabled_with_dsn():
    from observability.sentry import init_sentry

    assert init_sentry('https://key@sentry.example.com/1') is True


def test_openapi_contract_request_examples():
    spec = client.get('/openapi.json').json()

    body = spec['paths']['/v1/analyze']['post']['requestBody']['content'][
        'application/json'
    ]
    assert body['schema']['$ref'] == '#/components/schemas/TextRequest'
    assert (
        'examples' in spec['components']['schemas']['TextRequest']['properties']['text']
    )


def test_docs_endpoints_available():
    assert client.get('/docs').status_code == 200
    assert client.get('/redoc').status_code == 200

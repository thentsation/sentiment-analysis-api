from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EXPECTED_PATHS = {
    '/': {'get'},
    '/health': {'get'},
    '/v1/analyze': {'post'},
    '/v1/analyze_multiple': {'post'},
    '/v1/analyze_statistics': {'post'},
    '/v1/sentiment_classes': {'get'},
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

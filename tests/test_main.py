from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_security_headers_present():
    response = client.get('/health')

    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
    assert 'Strict-Transport-Security' in response.headers


def test_cors_headers_present():
    response = client.get('/health', headers={'Origin': 'https://example.com'})

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == '*'


def test_cors_preflight():
    response = client.options(
        '/health',
        headers={
            'Origin': 'https://example.com',
            'Access-Control-Request-Method': 'GET',
        },
    )

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == '*'

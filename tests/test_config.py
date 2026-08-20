from config import Settings


def test_settings_defaults():
    settings = Settings()

    assert settings.version == '1.0.0'
    assert settings.host == '0.0.0.0'
    assert settings.port == 8000
    assert settings.log_level == 'info'
    assert settings.log_format == 'json'
    assert settings.workers == 1
    assert settings.rate_limit_per_minute == 100
    assert settings.cors_origins == ['*']
    assert settings.admin_token == ''
    assert settings.cache_maxsize == 10_000
    assert settings.cache_ttl_seconds == 300.0
    assert settings.job_store_maxsize == 100
    assert settings.sentry_dsn == ''
    assert settings.sentry_traces_sample_rate == 1.0


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv('PORT', '9000')
    monkeypatch.setenv('RATE_LIMIT_PER_MINUTE', '5')
    monkeypatch.setenv('CORS_ORIGINS', '["https://example.com"]')

    settings = Settings()

    assert settings.port == 9000
    assert settings.rate_limit_per_minute == 5
    assert settings.cors_origins == ['https://example.com']

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    version: str = '1.0.0'
    host: str = '0.0.0.0'
    port: int = 8000
    log_level: str = 'info'
    rate_limit_per_minute: int = 100
    cors_origins: list[str] = ['*']
    admin_token: str = ''
    cache_maxsize: int = 10_000
    cache_ttl_seconds: float = 300.0
    job_store_maxsize: int = 100


settings = Settings()

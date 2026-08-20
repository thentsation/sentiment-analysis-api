def init_sentry(dsn: str, traces_sample_rate: float = 1.0) -> bool:
    if not dsn:
        return False

    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn, send_default_pii=False, traces_sample_rate=traces_sample_rate
    )
    return True

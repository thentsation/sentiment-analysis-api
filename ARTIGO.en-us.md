[🇧🇷 Português](ARTIGO.md) | 🇺🇸 English

# From toy API to production: evolving a sentiment analysis API

How a ~100-line FastAPI app turned into a service with tests, CI, caching, multi-language support, async batch processing, SSE, and observability — with real benchmark numbers at the end.

## The starting point

The project started like most learning projects: a FastAPI app exposing VADER (NLTK) for sentiment analysis, organized in layers (`routes` → `services` → `repositories`), with a Dockerfile and a pipeline that ran `ruff` on `main`. It worked. And that was it.

The problem is that "it works on my machine" isn't an engineering criterion. It was missing everything that separates a tutorial example from a service you'd put your name on:

- Zero automated tests
- CI that only ran on push to `main`
- No error handling (any exception leaked its stack trace)
- `requirements.txt` with no version pinning — and a bug: a `routes` line listed as a PyPI dependency broke `pip install` on a clean environment
- A Dockerfile with `COPY ../` (which doesn't even work with a root-level build context) and running as root

This article is the path from there to here.

## First stop: the foundation (tests, CI, Docker)

Before any new feature, the foundation. The rule I followed: **no new code without a safety net underneath.**

### Tests in three layers

The application already had the `routes` → `services` → `repositories` separation, so the tests followed the same boundaries:

- **Repository** (`test_repository.py`): VADER is deterministic, so I tested clearly positive, negative, and neutral texts, checking the signs of the scores (`compound`, `pos`, `neg`, `neu`) — no mocks. When the dependency is fast and deterministic, mocking is just noise.
- **Service** (`test_service.py`): here the repository is mocked, because what matters is the business logic — threshold-based classification (`> 0.05`, `< -0.05`), statistics aggregation, boundary values.
- **Routes** (`test_routes.py`): the endpoints via `TestClient`, covering success as well as 400 errors (empty text/list) and 422 errors (payload over the limits).

### CI that runs on every commit

The original pipeline only ran on `main` — meaning you'd find out you broke something *after* the merge. I changed it to run on every push and PR, with parallel jobs: lint, format check, mypy, and tests with a minimum coverage threshold across a Python 3.11/3.12 matrix.

### Docker without surprises

A multi-stage Dockerfile based on `python:3.12-slim`, a non-root user, and — an important detail — the **VADER lexicon pre-downloaded at build time**. Without that, the first request in production would depend on a runtime download. Cold start shouldn't depend on the network.

```dockerfile
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/usr/local/share/nltk_data')"
```

## The API itself: contract first

With the foundation in place, the next step was to treat the API as a **product with a contract**, not as an HTTP script:

- **Versioning** (`/v1/...`): lets you evolve the API without breaking clients.
- **Rich OpenAPI**: `response_model`, `summary`, `description`, examples, and tags on every endpoint. Typed response schemas (`AnalyzeResponse`, `SentimentScores`) instead of loose dictionaries — if the contract lives in the type, mypy and `/docs` do the work for you.
- **Payload validation**: `Field(max_length=10_000)` on the text and `max_length=100` on the list. A public API with no size limit is a toy DoS just waiting to happen.
- **`GET /`** with metadata and **`GET /health`** for liveness probes.

## Features worth a paragraph each

### Multi-language: VADER for English, LeIA for Portuguese

VADER only understands English. For PT-BR, I used [LeIA](https://github.com/RafJaa/LeIA) — a VADER fork adapted for Portuguese. The integration is a dispatcher in the repository:

```python
ANALYZERS = {
    'en': VaderAnalyzer(),
    'pt': LeiaAnalyzer(),
}

def analyze_sentiment(text: str, language: str = 'en') -> dict[str, float]:
    analyzer = ANALYZERS.get(language)
    if analyzer is None:
        raise ValueError(f'Unsupported language: {language}')
    return analyzer.polarity_scores(text)
```

A fun fact that earned its own "lessons learned" entry: the `leia` package published on PyPI is an **empty stub** — the real project was never packaged. The fix: I vendored the module (single file + lexicons) into `src/vendor/leia/`, excluding that folder from lint and mypy. Third-party code under my own version control, immutable and auditable.

### Caching: the cheapest, most profitable feature

Sentiment analysis is pure CPU-bound work and **deterministic**: same text, same score, every time. It's the perfect caching use case. I implemented an in-memory cache with TTL and LRU eviction, keyed by `(language, text)`:

```python
def analyze_sentiment(self, text: str, language: str = 'en') -> dict[str, float]:
    if self._cache is not None:
        cached = self._cache.get(text, language)
        if cached is not None:
            return cached
    result = analyze_sentiment(text, language)
    if self._cache is not None:
        self._cache.set(text, language, result)
    return result
```

Workloads with repeated texts (reviews, social media, monitoring) get a high hit rate — and the numbers at the end show the payoff.

### Async batch with job ID

A large batch shouldn't hold the connection open. `POST /v1/analyze_batch` responds with `202 Accepted` and a job ID right away; processing runs in the background, and the client polls `GET /v1/results/{job_id}` until `completed` (or `failed`).

### Streaming with SSE

For anyone who wants progressive results, `POST /v1/analyze_stream` responds with Server-Sent Events: one `data` event per analyzed text, ending with `event: done`. Simple, works with a plain `curl -N`, and doesn't need WebSocket.

## Observability: you can't fix what you can't see

- **`GET /metrics` in Prometheus format**: HTTP counters by method/route/status, a latency histogram, sentiment distribution by language, cache hits/misses, and job counts by status.
- **Structured logging (structlog)** in JSON, with a `request_id` generated per request (or propagated from the client via `X-Request-ID`). When something breaks, you filter by an ID and see the exact line.
- **`X-Process-Time-Ms` header** on every response.
- **Optional Sentry** — set `SENTRY_DSN` and you're done, no code changes needed.
- **Rate limiting** per IP (429 + `Retry-After`) and security headers.

Everything is configurable via environment variables through `pydantic-settings`, with a `make dev` target that boots with reload for day-to-day work.

## The numbers (the part that matters)

Full methodology in the repository (`docs/benchmarks/`), but the summary: locust, 20 virtual users, 30s per scenario, 1 worker, short texts:

| Scenario | req/s | p50 | p95 | p99 |
| --- | --- | --- | --- | --- |
| Cache hit (EN) | **971** | 18ms | 30ms | 53ms |
| Cache miss (EN, VADER) | 568 | 33ms | 60ms | 93ms |
| Cache miss (PT, LeIA) | 458 | 41ms | 95ms | 140ms |

**+71% throughput and -45% p50 latency** just from not recomputing what was already computed. Zero failures across every scenario. LeIA is ~20% slower than VADER (bigger lexicon + accent normalization), but it's far from a bottleneck.

## Lessons the tutorial doesn't tell you

1. **PyPI sometimes lies.** Check what you install — the `leia` package there was an empty file. Vendoring small, stable code is a legitimate option.
2. **Code coverage needs context.** The vendored code was dragging the metric down to 33%. Excluding `src/vendor` from coverage reported the right number: **98% coverage on the 412 lines that are actually mine**.
3. **In-memory state has an owner.** With `WORKERS > 1`, each process gets its own cache and job store. For this use case (the cache is just an optimization, the job store is ephemeral) that's acceptable — but it's a conscious, documented decision, not an accident. If global consistency is ever needed, the next step is Redis.
4. **`app.mount('/metrics')` in FastAPI returns a 307** for `/metrics` (redirecting to `/metrics/`). Prometheus doesn't follow redirects. The fix was to expose it as a regular route using `generate_latest()`.
5. **Small, green commits.** Every feature was one commit with lint, types, and tests passing. The `git log` became the article's narrative.

## Final state

- 72 tests, 98% coverage, a 90% threshold gating CI
- ruff (lint + format) and mypy clean, running on every push
- CI across a Python matrix, Docker build validated on every push
- Versioned, documented API with caching, batch, streaming, rate limiting, and metrics
- Reproducible benchmark via `make benchmark`

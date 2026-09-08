[🇧🇷 Português](ARTIGO.md) | 🇺🇸 English

# Taking an API I wrote in one afternoon seriously

The first version of this API was about 100 lines, ran VADER over English text, and was exactly what it sounds like: an exercise. I decided to treat it like it was actually going to production, and that changed almost everything — except the original idea.

## What I started with

A FastAPI app exposing VADER (NLTK) for sentiment analysis, already organized in layers (`routes` → `services` → `repositories`), with a Dockerfile and a pipeline that ran `ruff` on `main`. It ran. That was it.

"Works on my machine" isn't an engineering criterion, and I knew that while writing it. It was missing everything that separates a tutorial example from something I'd put my name on: zero automated tests, CI that only ran after a push to `main` (meaning I'd find out I broke something after the merge), no error handling at all — any exception leaked its stack trace to the client —, an unpinned `requirements.txt` with an amusing bug of its own — a `routes` line listed as a PyPI dependency that broke `pip install` on a clean environment — and a Dockerfile with `COPY ../` (which doesn't even work with a root-level build context) running as root.

## The rule I followed: no new feature without a safety net underneath

Before touching anything new, I built the foundation.

The app already had the `routes` → `services` → `repositories` split, so the tests followed the same boundaries. At the **repository** layer (`test_repository.py`), VADER is deterministic, so I tested clearly positive, negative, and neutral texts, checking the sign of the scores (`compound`, `pos`, `neg`, `neu`) with no mocks at all — when the dependency is fast and deterministic, mocking is just noise. At the **service** layer (`test_service.py`), the repository is mocked because what matters there is the business logic: threshold-based classification (`> 0.05`, `< -0.05`), statistics aggregation, boundary values. At the **routes** layer (`test_routes.py`), the endpoints via `TestClient`, covering success plus the 400s (empty text/list) and 422s (payload over the limits).

The original pipeline only ran on `main`; I changed it to run on every push and PR, with parallel jobs — lint, format check, mypy, and tests with a minimum coverage threshold across a Python 3.11/3.12 matrix.

Docker got a multi-stage rebuild on `python:3.12-slim`, a non-root user, and one detail I almost skipped: the **VADER lexicon pre-downloaded at build time**.

```dockerfile
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/usr/local/share/nltk_data')"
```

Without that, the first production request would depend on a runtime download — and cold start shouldn't depend on the network.

## Treating the API as a contract, not an HTTP script

With the foundation in place, the next step was to stop thinking of this as "an endpoint that returns JSON" and start thinking of it as a contract: versioning under `/v1/...` so I can evolve it without breaking anyone already integrated; a rich OpenAPI spec, with `response_model`, `summary`, `description`, examples, and tags on every endpoint; typed response schemas (`AnalyzeResponse`, `SentimentScores`) instead of loose dictionaries, because if the contract lives in the type, mypy and `/docs` do the work for me; payload validation (`Field(max_length=10_000)` on the text, `max_length=100` on the list) — a public API with no size limit is a toy DoS waiting to happen; and `GET /` with metadata plus `GET /health` for liveness probes.

## Decisions worth a paragraph each

**Multi-language without rewriting the pipeline.** VADER only understands English. For PT-BR I used [LeIA](https://github.com/RafJaa/LeIA), a VADER fork adapted for Portuguese, plugged in as a simple dispatcher in the repository:

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

The detail that turned into an important footnote: the `leia` package published on PyPI is an **empty stub** — the real project was never packaged properly. I fixed it by vendoring the module (single file + lexicons) into `src/vendor/leia/`, excluded from lint and mypy. Third-party code under my own version control, immutable and auditable, instead of depending on a broken package on PyPI.

**Caching, because the workload is deterministic.** Sentiment analysis here is pure CPU-bound work and deterministic — same text, same score, every time. It's the perfect caching use case. I implemented an in-memory cache with TTL and LRU eviction, keyed by `(language, text)`:

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

Workloads with repeated text (reviews, social media, monitoring) get a high hit rate, and the numbers below show the payoff.

**Batch without holding the connection.** `POST /v1/analyze_batch` responds with `202 Accepted` and a job ID right away; processing runs in the background, and the client polls `GET /v1/results/{job_id}` until `completed` (or `failed`).

**Streaming without WebSocket.** For anyone who wants progressive results, `POST /v1/analyze_stream` responds with Server-Sent Events — one `data` event per analyzed text, ending with `event: done`. Works with a plain `curl -N`.

## I can't fix what I can't see

`GET /metrics` in Prometheus format, with HTTP counters by method/route/status, a latency histogram, sentiment distribution by language, cache hits/misses, and job counts by status. Structured logging (`structlog`) in JSON, with a `request_id` per request — generated or propagated via `X-Request-ID` — because when something breaks I want to filter by an ID and see the exact line, not hunt through free text. An `X-Process-Time-Ms` header on every response. Optional Sentry, switched on just by setting `SENTRY_DSN`. Rate limiting per IP (429 + `Retry-After`) and security headers. Everything configurable via environment variables through `pydantic-settings`, with a `make dev` target that boots with reload for day-to-day work.

## The numbers

Full methodology lives in `docs/benchmarks/`; the summary is locust with 20 virtual users, 30s per scenario, 1 worker, short texts:

| Scenario | req/s | p50 | p95 | p99 |
| --- | --- | --- | --- | --- |
| Cache hit (EN) | **971** | 18ms | 30ms | 53ms |
| Cache miss (EN, VADER) | 568 | 33ms | 60ms | 93ms |
| Cache miss (PT, LeIA) | 458 | 41ms | 95ms | 140ms |

+71% throughput and -45% p50 latency just from not recomputing what was already computed, zero failures across every scenario. LeIA is about 20% slower than VADER — bigger lexicon, accent normalization — but it's far from a bottleneck.

## What I'm taking from this one

PyPI sometimes lies — checking what you install is part of the job, not paranoia; vendoring small, stable code is a legitimate option when the official package is broken. Code coverage also needs context: the vendored code was dragging the metric down to 33%, and excluding `src/vendor` from coverage revealed the real number — 98% on the 412 lines that are actually mine. In-memory state has an owner: with `WORKERS > 1`, each process gets its own cache and job store; for this use case that's acceptable, but it was a conscious, documented decision, not an accident — if global consistency is ever needed, the next step is Redis. And one FastAPI-specific gotcha: `app.mount('/metrics')` returns a 307 (redirecting to `/metrics/`), and Prometheus doesn't follow redirects — I fixed it by exposing it as a regular route with `generate_latest()`. Finally, every feature became its own commit with lint, types, and tests green before the next one — the `git log` ended up being the most honest narrative of this whole process.

## Where the API stands now

72 tests, 98% coverage, a 90% threshold gating CI. `ruff` (lint + format) and `mypy` clean on every push, CI across a Python matrix, Docker build validated on every push. Versioned, documented API with caching, batch, streaming, rate limiting, and metrics. Reproducible benchmark via `make benchmark`.

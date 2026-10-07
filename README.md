[🇧🇷 Português](README.pt-br.md) | 🇺🇸 English

# Sentiment Analysis API

FastAPI application that performs sentiment analysis on text inputs using NLTK VADER (English) and LeIA (Portuguese).

## Features

- Analyze the sentiment of a single text or multiple texts (EN/PT).
- Async batch analysis: submit large batches and poll results by job id.
- Progressive analysis streaming via Server-Sent Events (SSE).
- Result caching with TTL and admin invalidation endpoint.
- Rate limiting, security headers and CORS.
- Observability: Prometheus `/metrics`, structured logging with request ids, Sentry integration.
- Health check and API metadata endpoints.
- Versioned API under `/v1` with rich OpenAPI documentation.

## Requirements

- Python 3.11 or higher
- FastAPI, Uvicorn, NLTK (see `config/requirements.txt`)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ntsation/sentiment-analysis-api.git
   cd sentiment-analysis-api
   ```

2. Create the virtual environment and install dependencies:

   ```bash
   make install
   ```

   Or manually:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r config/requirements.txt
   ```

## Usage

1. Run the application:

   ```bash
   make run
   ```

   The API will start on `http://127.0.0.1:8000`.

2. For development with auto-reload:

   ```bash
   make dev
   ```

### Make targets

| Target | Description |
| --- | --- |
| `make install` | Creates `.venv` and installs dependencies (runtime + dev) |
| `make run` | Runs the application |
| `make dev` | Runs with auto-reload (uvicorn) |
| `make test` | Runs the test suite |
| `make coverage` | Runs tests with coverage report |
| `make lint` | Runs `ruff check .` |
| `make format` | Runs `ruff format .` |
| `make typecheck` | Runs `mypy` |
| `make load-test` | Runs the locust load test UI |
| `make benchmark` | Runs the cache benchmark (hit vs miss, EN/PT) — requires the server running with `RATE_LIMIT_PER_MINUTE` high |
| `make docker-build` | Builds the Docker image |
| `make docker-run` | Runs the Docker container on port 8000 |
| `make clean` | Removes caches and artifacts |

### Configuration

Settings are read from environment variables (or a `.env` file — see `.env.example`):

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `info` | Uvicorn log level |
| `LOG_FORMAT` | `json` | Log format: `json` or `console` |
| `WORKERS` | `1` | Uvicorn worker processes |
| `RATE_LIMIT_PER_MINUTE` | `100` | Requests per minute per client |
| `CORS_ORIGINS` | `["*"]` | Allowed origins (JSON list) |
| `ADMIN_TOKEN` | _(empty)_ | When set, `DELETE /v1/cache` requires `X-Admin-Token` |
| `CACHE_MAXSIZE` | `10000` | Maximum cached sentiment entries |
| `CACHE_TTL_SECONDS` | `300` | Cache entry TTL |
| `JOB_STORE_MAXSIZE` | `100` | Maximum in-memory batch jobs kept |
| `SENTRY_DSN` | _(empty)_ | Enables Sentry error tracking when set |
| `SENTRY_TRACES_SAMPLE_RATE` | `1.0` | Sentry traces sample rate |

Note: with `WORKERS > 1` each worker keeps its own in-memory cache, job store and
metrics registry (per-process). Use a single worker or an external shared store if
global consistency is required.

### Pre-commit hooks

Install the hooks (lint + format on every commit):

```bash
pre-commit install
```

### Docker

```bash
make docker-build
make docker-run
```

Or with docker compose:

```bash
docker compose up --build
```

### Load testing

Start the API and run the locust UI (http://localhost:8089):

```bash
make run
make load-test
```

Headless example:

```bash
.venv/bin/locust -f load_tests/locustfile.py --host http://localhost:8000 \
  --headless -u 50 -r 5 --run-time 30s
```

### Benchmark

Cache hit vs cache miss benchmark (results and methodology in
[`docs/benchmarks/`](docs/benchmarks/)):

```bash
RATE_LIMIT_PER_MINUTE=1000000 make run
make benchmark
```

## API Endpoints

Interactive documentation is available at `/docs` (Swagger) and `/redoc`.

### Meta

- **GET /** — API metadata (name, version, docs, endpoints list).
- **GET /health** — Health check.
- **GET /metrics** — Prometheus metrics (HTTP request counters, latency histogram,
  sentiment distribution by language, cache hits/misses, batch job counters).

### Sentiment (`/v1`)

- **POST /v1/analyze** — Analyze a single text (max 10,000 characters).
  - **Request Body:**
    ```json
    {
      "text": "I love this!",
      "language": "en"
    }
    ```
    `language` is optional (`en` or `pt`, defaults to `en`).
  - **Response:**
    ```json
    {
      "text": "I love this!",
      "language": "en",
      "sentiment": {
        "neg": 0.0,
        "neu": 0.182,
        "pos": 0.818,
        "compound": 0.6696
      }
    }
    ```

- **POST /v1/analyze_multiple** — Analyze multiple texts (max 100), keyed by text.

- **POST /v1/analyze_statistics** — Count positive/neutral/negative texts.

- **GET /v1/sentiment_classes** — Classification thresholds.

### Batch (`/v1`)

- **POST /v1/analyze_batch** — Submit a batch for asynchronous analysis. Returns
  `202 Accepted` with a job id immediately:
  ```json
  {
    "job_id": "e2b1...",
    "status": "pending",
    "total": 2,
    "results_url": "/v1/results/e2b1..."
  }
  ```

- **GET /v1/results/{job_id}** — Poll job status (`pending`, `processing`,
  `completed`, `failed`); includes per-text results once completed. Returns `404`
  for unknown or evicted jobs.

### Streaming (`/v1`)

- **POST /v1/analyze_stream** — Server-Sent Events response with one `data`
  event per analyzed text, followed by a final `event: done`.

### Admin (`/v1`)

- **DELETE /v1/cache** — Invalidate the sentiment cache. Requires the
  `X-Admin-Token` header when `ADMIN_TOKEN` is configured.

## CI/CD

- **pipeline_python.yaml** — on every push/PR: `ruff check`, `ruff format --check`,
  `pytest` with coverage (Python 3.11 and 3.12) and `mypy`.
- **pipeline_docker.yaml** — on every push/PR: builds the Docker image.

## Project structure

```
src/
├── config.py              # Pydantic settings (env-driven)
├── main.py                # App factory, middlewares, meta routes
├── middlewares/           # Rate limit, security headers, metrics, request context
├── models/                # Request/response schemas
├── observability/         # Prometheus metrics, structlog, Sentry
├── repositories/          # Analyzer dispatch (VADER/LeIA)
├── routes/                # /v1 endpoints
├── services/              # Business logic, cache, job store
└── vendor/                # Vendored third-party code (LeIA)
```

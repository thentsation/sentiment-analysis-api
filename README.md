[🇧🇷 Português](README.pt-br.md) | 🇺🇸 English

# Sentiment Analysis API

Sentiment analysis on text with VADER (English) and LeIA (Portuguese), written in [Telvax](https://github.com/telvax/telvax).
The service is one program with the same layout as the Python service (`src/main.tvx`, `config`, `models`, `routes`, `services`, `vendor/leia`) and runs as one binary with the lexicons
inside it. It started as a FastAPI application; the scores of the two versions are the same (see [Tests](#tests)).

## Features

- Analyze the sentiment of a single text or multiple texts (EN/PT).
- Async batch analysis: submit large batches and poll results by job id; with `DATABASE_URL` the jobs survive a restart.
- Progressive analysis streaming via Server-Sent Events (SSE).
- Result caching with TTL and admin invalidation endpoint.
- Rate limiting, security headers and CORS.
- Observability: Prometheus `/metrics`, JSON logs with request ids.
- Health check and API metadata endpoints.
- Versioned API under `/v1` with an OpenAPI document generated from the types.

## Requirements

- The `telvax` command, or Docker. See [telvax/telvax](https://github.com/telvax/telvax) to install it.

## Usage

```bash
make run          # http://127.0.0.1:8000
make dev          # text logs
make test         # the scores against the Python service
make api-test     # calls every route of a running server
make build        # one binary: ./sentiment-analysis-api
```

`make run` is `telvax serve src/main.tvx --port 8000 --metrics --log-format json --cors '*' --rate-limit 100/min --security-headers`.

### Make targets

| Target | Description |
| --- | --- |
| `make run` | Runs the application |
| `make dev` | Runs with text logs |
| `make check` | Type-checks the program |
| `make test` | Runs the tests |
| `make format` | Formats `src/` |
| `make lint` | Format check and lint |
| `make build` | Makes one binary with the program and the lexicons |
| `make api-test` | Calls every route of a server that is running |
| `make load-test` | Runs the Locust load test UI (Locust is installed in `.venv`) |
| `make benchmark` | Runs the cache benchmark (hit vs miss, EN/PT); the rate limit has to be high |
| `make docker-build` | Builds the Docker image |
| `make docker-run` | Runs the Docker container on port 8000 |
| `make clean` | Removes `.venv` and the binary |

### Configuration

The service reads environment variables. The first four are read by every binary made with `telvax build --serve`:

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8080` (`8000` in the image) | Bind port; `--port` wins |
| `TELVAX_LOG_FORMAT` | _(none)_ | `json` or `text`: one log line per request, with a request id |
| `TELVAX_RATE_LIMIT` | _(none)_ | Requests per client address, as `100/min` |
| `TELVAX_CORS` | _(none)_ | Allowed origins, `*` or a comma-separated list |
| `TELVAX_METRICS` | _(none)_ | `1` serves `/metrics` |
| `TELVAX_SECURITY_HEADERS` | _(none)_ | `1` adds the security headers |
| `ADMIN_TOKEN` | _(empty)_ | When set, `DELETE /v1/cache` requires `X-Admin-Token` |
| `CACHE_MAXSIZE` | `10000` | Maximum cached sentiment entries |
| `CACHE_TTL_SECONDS` | `300` | Cache entry TTL |
| `JOB_STORE_MAXSIZE` | `100` | Maximum in-memory batch jobs kept |
| `DATABASE_URL` | _(empty)_ | Keeps the batch jobs in PostgreSQL (also needs `TELVAX_LIVE=1`) |

Notes:

- One process serves all requests, so the cache, the jobs and the counters are shared by all of them; there is no
  `WORKERS` setting. Run several containers behind a load balancer and use `DATABASE_URL` if jobs must be seen by all.
- When the cache is full, the entry that goes is the first key in order, not the oldest.
- An error in the body of a request is a `400` with `{"error": "invalid request", "details": [...]}`; a value the
  service rejects (a text over 10,000 characters, a language other than `en` or `pt`, more than 100 texts) is a `422`
  with `{"detail": "..."}`, as the other errors of the service.

### Docker

```bash
make docker-build
make docker-run
```

Or with docker compose:

```bash
docker compose up --build
```

The image builds the program with `ghcr.io/telvax/telvax` and ships only the binary on a distroless base. Its health check
is `/service --healthcheck /health`.

### Tests

`src/leia_test.tvx` has 45 texts (English and Portuguese) with the scores that the Python service gave; they were made
by running NLTK VADER and the vendored LeIA of the previous version over the texts. A further 800 random sentences
(lexicon words, negations, capitals, punctuation, accents, emoji) gave the same scores in both versions.

```bash
make test
```

### Load testing

Start the API and run the Locust UI (http://localhost:8089):

```bash
make run
make load-test
```

### Benchmark

Cache hit vs cache miss benchmark (results and methodology in [`docs/benchmarks/`](docs/benchmarks/)):

```bash
telvax serve src/main.tvx --rate-limit 1000000/min
make benchmark
```

## API Endpoints

Interactive documentation is available at `/docs`; the OpenAPI document is at `/openapi.json`.

### Meta

- **GET /** — API metadata (name, version, docs, endpoints list).
- **GET /health** — Health check.
- **GET /metrics** — Prometheus metrics: requests and latency per route, and the counters of the
  service as `telvax_counter_total{name="..."}` (`cache_hits`, `cache_misses`,
  `sentiment_analysis_<language>_<class>`, `batch_jobs_<status>`).

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

- **pipeline_telvax.yaml** — on every push/PR: `telvax check`, `fmt --check`, `lint`, the tests, and a container that is
  built, waits for its health check and is called on every route by `tests/api.sh`.
- **pipeline_docker.yaml** — on every push/PR: builds the Docker image and scans it.

## Project structure

```
src/
├── main.tvx                       # App: root and health routes
├── config.tvx                     # Settings from the environment
├── db.tvx                         # PostgreSQL storage of the jobs
├── models/
│   └── models.tvx                 # Request and answer types, limits on a request
├── repositories/
│   └── sentiment_repository.tvx   # The analysis of one text
├── routes/
│   └── sentiment_routes.tvx       # The /v1 routes: analysis, cache, batch jobs, SSE
├── services/
│   ├── cache_service.tvx          # Cache of scores
│   ├── job_store.tvx              # Batch jobs, in memory and in PostgreSQL
│   └── sentiment_service.tvx      # Sentiment through the cache, classes
├── vendor/leia/
│   ├── leia.tvx                   # VADER and LeIA
│   └── lexicons/                  # The lexicons, embedded in the binary
└── *_test.tvx                     # Tests: models, services and scores against the Python service
tests/
└── api.sh                         # Calls every route of a running server
```

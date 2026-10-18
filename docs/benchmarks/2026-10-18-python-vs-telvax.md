# Benchmark: Python (FastAPI) vs Telvax

Data: 2026-10-18

## Method

- **Tool:** `ab` (Apache Bench), 20 concurrent connections, no keep-alive, 2,000 requests per cache-miss scenario and 3,000
  for the cache hit; client and server on the same machine (loopback, macOS, Apple Silicon).
- **Python:** the service at commit `24b5878`, uvicorn with 1 worker, Python 3.12.14, `RATE_LIMIT_PER_MINUTE=100000000`.
- **Telvax:** `src/main.tvx` run by `telvax serve` (release build of the compiler), `--rate-limit 100000000/min`.
- **Endpoint:** `POST /v1/analyze` with one text of about 60 characters.
- **Cache miss:** `CACHE_TTL_SECONDS=0.00001` (Python) and `0` (Telvax), so every request runs the analyzer. The Telvax run
  was checked with `/metrics`: 500 requests gave 500 `cache_misses` and 500 analyses.
- Only a single machine and a short run: the numbers are for comparing the two on one setup, not absolute.

## Results

| Scenario | Python req/s | Telvax req/s | Ratio |
| --- | --- | --- | --- |
| Cache hit (EN) | 1,305 | 41,236 | 31.6x |
| Cache miss (EN, VADER) | 1,128 | 10,161 | 9.0x |
| Cache miss (PT, LeIA) | 1,011 | 8,821 | 8.7x |

Resident memory after the runs: Python 83 MB, Telvax 30 MB.

## Notes

- In Python the analyzers alone take 0.03 ms (VADER) and 0.04 ms (LeIA) per text, measured with `timeit`, while a request
  costs about 0.9 ms: the time goes to the web layers (five `BaseHTTPMiddleware`, Pydantic, the response model). The ratio
  on a cache miss is therefore a measure of the whole service, not of the scoring code alone.
- The older numbers in `2026-08-20-cache-benchmark.md` were taken with Locust on another setup.

## Second run: more scenarios (same machine, 10 cores)

`ab`, no keep-alive. Python with 1 worker and with 10 workers (`--workers 10`); Telvax is one process.

| Scenario | Python 1 worker | Python 10 workers | Telvax |
| --- | --- | --- | --- |
| Cache hit EN, 1 connection | 783 req/s | - | 13,617 req/s |
| Cache hit EN, 20 connections (p50 / p99) | 1,296 (15 / 26 ms) | - | 42,734 (0 / 1 ms) |
| Cache hit EN, 100 connections (p50 / p99) | 1,170 (87 / 127 ms) | - | 40,047 (2 / 6 ms) |
| Cache miss EN, 20 connections (p50 / p99) | 1,232 (15 / 28 ms) | 3,205 (6 / 20 ms) | 11,953 (2 / 5 ms) |
| Cache miss PT, 20 connections (p50 / p99) | 1,178 (16 / 27 ms) | 3,168 (6 / 11 ms) | 9,799 (2 / 4 ms) |
| `analyze_multiple`, 100 texts, miss, 10 connections | 260 | 1,056 | 162 |

Resident memory after the runs: Python 83 MB with 1 worker and 270 MB with 10; Telvax 32 MB.
Start until `/health` answers: Python 0.31 s, Telvax 0.06 s.

Where Python is ahead: scoring itself. A request with 100 texts costs about 15 ms in Telvax with one connection and
about 4 ms in Python (`timeit` gives 0.03 ms a text for VADER), so a service that mostly receives large batches is
faster in Python today. The Telvax analyzer is interpreted; it runs on several threads but stops scaling at about four
connections on this machine.

Size and effort: the Telvax program is 789 lines (both analyzers included) against 949 lines of Python plus the 574 of the
vendored LeIA and the NLTK package; one 69 MB binary against 9 direct dependencies (32 locked packages, 52 MB of
site-packages). The Python tests are 781 lines (unit tests of cache, job store and middleware, 90% coverage gate); the
Telvax tests are the 45 fixed texts and `tests/api.sh`, so the unit coverage of the cache and the job store is lower.

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

- The Python service spends most of its time in five `BaseHTTPMiddleware` layers and Pydantic; the same text analyzed
  directly takes far less than the 0.9 ms a request costs. The ratio on a cache miss is therefore a measure of the whole
  service, not of the VADER code alone.
- The older numbers in `2026-08-20-cache-benchmark.md` were taken with Locust on another setup.

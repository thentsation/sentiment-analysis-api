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

## Third run, after optimizing the interpreter

The Telvax numbers above are from the first version of the program on the first version of the interpreter, and in one
scenario (100 texts per request) it was behind Python. This run uses the changes of telvax/telvax#166 and a tokenizer
that makes one regular-expression call per word instead of one per character. Each cell is the median of three `ab` runs
(Python 3.12, 10 cores, no keep-alive); the scores of the 45 fixed texts and of 800 random sentences are unchanged.

| Scenario | Python 1 worker | Python 10 workers | Telvax | Telvax vs best Python |
| --- | --- | --- | --- | --- |
| Cache miss EN, 20 connections | 1,172 req/s | 3,153 | 36,629 | 11.6x |
| Cache miss PT, 20 connections | 1,171 | 2,690 | 36,681 | 13.6x |
| 100 texts per request, 1 connection | 227 | 209 | 282 | 1.24x |
| 100 texts per request, 10 connections | 259 | 978 | 1,269 | 1.30x |
| Cache hit EN, 1 connection | 741 | 658 | 14,404 | 19.4x |
| Cache hit EN, 20 connections | 1,263 | 3,312 | 50,847 | 15.4x |
| Cache hit EN, 100 connections | 1,192 | 3,700 | 46,711 | 12.6x |

Latency at 20 connections on a cache miss: p50 16 ms and p99 28 ms for Python with one worker, 6 ms and 23 ms with ten,
1 ms and 1 ms for Telvax. With 100 texts per request and 10 connections: Python 38 / 48 ms (1 worker), 9 / 21 ms
(10 workers); Telvax 7 / 12 ms.

What changed in the program: the tokenizer, which was 60% of the time, now calls one pattern per word; the index of a
repeated word comes from a map instead of a scan of the list. What changed in the interpreter is in the telvax/telvax#166
description.

The margin on 100 texts per request is the thinnest, 24% to 30%; that is the scenario where scoring, not the web layer,
decides, and the Telvax scorer is still an interpreter running about as fast as the Python one on a single thread.

## Fourth run, with the eight changes of the second round

The program now uses `std.cache` (least recently used, expiry), counters with labels, `on_error` for failed jobs, the
error format of FastAPI and the time header (telvax/telvax#166, #175 to #179). Same method as the third run: the median
of three `ab` runs, Python 3.12, 10 cores, no keep-alive; 52 tests pass (45 fixed texts and 7 of the cache, the limits and
the job store), `tests/api.sh` passes 28 checks, and 800 random sentences still give the same scores as Python.

| Scenario | Python 1 worker | Python 10 workers | Telvax | Telvax vs best Python | Third run |
| --- | --- | --- | --- | --- | --- |
| Cache miss EN, 20 connections | 1,244 req/s | 3,368 | 44,193 | 13.1x | 36,629 |
| Cache miss PT, 20 connections | 1,219 | 3,359 | 45,046 | 13.4x | 36,681 |
| 100 texts per request, 1 connection | 232 | 218 | 284 | 1.22x | 282 |
| 100 texts per request, 10 connections | 265 | 1,074 | 1,362 | 1.27x | 1,269 |
| Cache hit EN, 1 connection | 773 | 710 | 14,496 | 18.8x | 14,404 |
| Cache hit EN, 20 connections | 1,278 | 3,567 | 53,061 | 14.9x | 50,847 |
| Cache hit EN, 100 connections | 1,236 | 4,628 | 49,382 | 10.7x | 46,711 |

Telvax is ahead in every scenario. The scenario with the least room is the same as before, 100 texts per request: the work
there is the scorer itself, an interpreter that runs about as fast as CPython on one thread and uses the cores better. gains over the third run (up to 20% for single texts, 7% for the batch) were not traced to a cause; a run-to-run variation of that size is possible on one machine.

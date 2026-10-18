.PHONY: run dev check test format lint build docker-build docker-run api-test load-test benchmark clean

TELVAX ?= telvax
PORT ?= 8000
VENV := .venv

run:
	$(TELVAX) serve src/main.tvx --port $(PORT) --metrics --log-format json --cors '*' --rate-limit 100/min --security-headers --error-format detail --process-time-header

dev:
	$(TELVAX) serve src/main.tvx --port $(PORT) --metrics --log-format text

check:
	$(TELVAX) check src/main.tvx

test:
	$(TELVAX) test src

format:
	$(TELVAX) fmt src

lint:
	$(TELVAX) fmt --check src
	$(TELVAX) lint src/main.tvx
	$(TELVAX) lint src/analyzer.tvx

build:
	$(TELVAX) build --serve src/main.tvx -o sentiment-analysis-api

# Calls a server that is already running (make run) on every route.
api-test:
	tests/api.sh http://127.0.0.1:$(PORT)

# The load tests are Locust scripts: they only call the HTTP API, so they stay in Python.
$(VENV)/bin/locust:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet locust

load-test: $(VENV)/bin/locust
	$(VENV)/bin/locust -f load_tests/locustfile.py --host http://localhost:$(PORT)

BENCH_HOST ?= http://localhost:$(PORT)
BENCH_USERS ?= 20
BENCH_TIME ?= 30s

benchmark: $(VENV)/bin/locust
	@echo "== Cache hit ==" && $(VENV)/bin/locust -f load_tests/benchmark.py CacheHitUser --host $(BENCH_HOST) --headless -u $(BENCH_USERS) -r $(BENCH_USERS) -t $(BENCH_TIME) --only-summary
	@echo "== Cache miss ==" && $(VENV)/bin/locust -f load_tests/benchmark.py CacheMissUser --host $(BENCH_HOST) --headless -u $(BENCH_USERS) -r $(BENCH_USERS) -t $(BENCH_TIME) --only-summary
	@echo "== PT-BR cache miss ==" && $(VENV)/bin/locust -f load_tests/benchmark.py PtCacheMissUser --host $(BENCH_HOST) --headless -u $(BENCH_USERS) -r $(BENCH_USERS) -t $(BENCH_TIME) --only-summary

docker-build:
	docker build -f docker/Dockerfile -t sentiment-analysis-api .

docker-run:
	docker run --rm -p 8000:8000 sentiment-analysis-api

clean:
	rm -rf $(VENV) sentiment-analysis-api

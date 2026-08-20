.PHONY: install run dev test coverage lint format typecheck load-test benchmark docker-build docker-run clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r config/requirements.txt
	$(PIP) install -r config/requirements-dev.txt

run:
	$(PYTHON) src/main.py

dev:
	$(VENV)/bin/uvicorn main:app --app-dir src --reload --host 0.0.0.0 --port 8000

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/ruff format .

typecheck:
	$(VENV)/bin/mypy

load-test:
	$(VENV)/bin/locust -f load_tests/locustfile.py --host http://localhost:8000

BENCH_HOST ?= http://localhost:8000
BENCH_USERS ?= 20
BENCH_TIME ?= 30s

benchmark:
	@echo "== Cache hit ==" && $(VENV)/bin/locust -f load_tests/benchmark.py CacheHitUser --host $(BENCH_HOST) --headless -u $(BENCH_USERS) -r $(BENCH_USERS) -t $(BENCH_TIME) --only-summary
	@echo "== Cache miss ==" && $(VENV)/bin/locust -f load_tests/benchmark.py CacheMissUser --host $(BENCH_HOST) --headless -u $(BENCH_USERS) -r $(BENCH_USERS) -t $(BENCH_TIME) --only-summary
	@echo "== PT-BR cache miss ==" && $(VENV)/bin/locust -f load_tests/benchmark.py PtCacheMissUser --host $(BENCH_HOST) --headless -u $(BENCH_USERS) -r $(BENCH_USERS) -t $(BENCH_TIME) --only-summary

docker-build:
	docker build -f docker/Dockerfile -t sentiment-analysis-api .

docker-run:
	docker run --rm -p 8000:8000 sentiment-analysis-api

clean:
	find . -type d -name __pycache__ -not -path './$(VENV)/*' -exec rm -rf {} +
	find . -type d -name .pytest_cache -not -path './$(VENV)/*' -exec rm -rf {} +
	find . -type f -name '*.pyc' -not -path './$(VENV)/*' -delete
	rm -f .coverage

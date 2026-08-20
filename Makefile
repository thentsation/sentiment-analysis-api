.PHONY: install run test coverage lint format docker-build docker-run clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r config/requirements.txt
	$(PIP) install ruff

run:
	$(PYTHON) src/main.py

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=src --cov-report=term-missing

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/ruff format .

docker-build:
	docker build -f docker/Dockerfile -t sentiment-analysis-api .

docker-run:
	docker run --rm -p 8000:8000 sentiment-analysis-api

clean:
	find . -type d -name __pycache__ -not -path './$(VENV)/*' -exec rm -rf {} +
	find . -type d -name .pytest_cache -not -path './$(VENV)/*' -exec rm -rf {} +
	find . -type f -name '*.pyc' -not -path './$(VENV)/*' -delete

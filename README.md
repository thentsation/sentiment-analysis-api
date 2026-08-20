# Sentiment Analysis API

This is a FastAPI application that performs sentiment analysis on text inputs using NLTK's VADER sentiment analysis tool.

## Features

- Analyze the sentiment of a single text input.
- Analyze the sentiment of multiple text inputs.
- Retrieve sentiment classification categories.
- Get statistics on sentiment distribution for multiple texts.
- Rate limiting, security headers and CORS.
- Health check endpoint.

## Requirements

- Python 3.11 or higher
- FastAPI
- Uvicorn
- NLTK

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
| `make install` | Creates `.venv` and installs dependencies |
| `make run` | Runs the application |
| `make dev` | Runs with auto-reload (uvicorn) |
| `make test` | Runs the test suite |
| `make coverage` | Runs tests with coverage report |
| `make lint` | Runs `ruff check .` |
| `make format` | Runs `ruff format .` |
| `make typecheck` | Runs `mypy` |
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
| `RATE_LIMIT_PER_MINUTE` | `100` | Requests per minute per client |
| `CORS_ORIGINS` | `["*"]` | Allowed origins (JSON list) |

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

### API Endpoints

- **POST /analyze**
  - Analyze sentiment of a single text (max 10,000 characters).
  - **Request Body:**
    ```json
    {
      "text": "Your text here"
    }
    ```
  - **Response:**
    ```json
    {
      "text": "Your text here",
      "sentiment": {
        "neg": 0.0,
        "neu": 0.4,
        "pos": 0.6,
        "compound": 0.5
      }
    }
    ```

- **POST /analyze_multiple**
  - Analyze sentiment of multiple texts (max 100 texts).
  - **Request Body:**
    ```json
    {
      "texts": ["Text one", "Text two"]
    }
    ```
  - **Response:**
    ```json
    {
      "results": {
        "Text one": { ... },
        "Text two": { ... }
      }
    }
    ```

- **GET /sentiment_classes**
  - Retrieve sentiment classification categories.
  - **Response:**
    ```json
    {
      "classes": {
        "positive": "Scores greater than 0.05",
        "neutral": "Scores between -0.05 and 0.05",
        "negative": "Scores less than -0.05"
      }
    }
    ```

- **POST /analyze_statistics**
  - Get statistics on the sentiment distribution for multiple texts.
  - **Request Body:**
    ```json
    {
      "texts": ["Text one", "Text two"]
    }
    ```
  - **Response:**
    ```json
    {
      "statistics": {
        "positive": 1,
        "neutral": 1,
        "negative": 0
      }
    }
    ```

- **GET /health**
  - Health check.
  - **Response:**
    ```json
    {
      "status": "ok"
    }
    ```

## CI/CD

- **pipeline_python.yaml** — on every push/PR: `ruff check`, `ruff format --check`, `pytest` with coverage (Python 3.11 and 3.12) and `mypy`.
- **pipeline_docker.yaml** — on every push/PR: builds the Docker image.

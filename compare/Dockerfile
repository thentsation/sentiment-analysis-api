# syntax=docker/dockerfile:1
# Runs the Python (FastAPI) and the Telvax version of this service, one after the other, under the same
# load, and prints a table. Build from the root of this repository:
#
#   docker build -f compare/Dockerfile -t sentiment-compare .
#   docker run --rm sentiment-compare
#
# The Python version is fetched from the commit of `main` named below; the Telvax version is the
# source in this checkout, built with the Telvax image named below.
ARG TELVAX_IMAGE=ghcr.io/telvax/telvax:0.44.0
ARG PYTHON_COMMIT=c03eb04a07bbf1b6c8abf1cb5c4ca73a80808cb9

FROM ${TELVAX_IMAGE} AS telvax
WORKDIR /app
COPY src ./src
RUN mkdir -p /out && telvax build --serve src/main.tvx -o /out/service

FROM python:3.14-slim-bookworm
ARG PYTHON_COMMIT
RUN apt-get update \
    && apt-get install -y --no-install-recommends apache2-utils libssl3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ADD https://github.com/thentsation/sentiment-analysis-api.git#${PYTHON_COMMIT} /python
RUN pip install --no-cache-dir -r /python/config/requirements.lock
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/usr/local/share/nltk_data')"
COPY --from=telvax /out/service /service
COPY compare/run.py /compare/run.py
ENV PYTHON_MAIN=/python/src/main.py TELVAX_SERVICE=/service
ENTRYPOINT ["python", "/compare/run.py"]

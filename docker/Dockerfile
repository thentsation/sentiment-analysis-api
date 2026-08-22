FROM python:3.14-slim AS builder

WORKDIR /app

COPY config/requirements.txt ./config/

RUN pip install --no-cache-dir --prefix=/install -r ./config/requirements.txt

FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /install /usr/local

ENV NLTK_DATA=/usr/local/share/nltk_data

RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/usr/local/share/nltk_data')"

RUN useradd --create-home appuser

USER appuser

COPY src ./src

EXPOSE 8000

CMD ["python", "src/main.py"]

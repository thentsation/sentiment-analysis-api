FROM python:3.12-slim AS builder

WORKDIR /app

COPY config/requirements.txt ./config/

RUN pip install --no-cache-dir --prefix=/install -r ./config/requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local

RUN useradd --create-home appuser

USER appuser

COPY src ./src

EXPOSE 8000

CMD ["python", "src/main.py"]

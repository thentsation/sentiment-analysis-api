import json
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg

from config import settings


@contextmanager
def _connect() -> Iterator[psycopg.Connection]:
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        yield conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sentiment_jobs (
                id TEXT PRIMARY KEY,
                language TEXT NOT NULL,
                total INTEGER NOT NULL,
                processed INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                results JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


def insert_job(job_id: str, language: str, total: int) -> None:
    with _connect() as conn:
        conn.execute(
            'INSERT INTO sentiment_jobs (id, language, total) VALUES (%s, %s, %s) '
            'ON CONFLICT (id) DO NOTHING',
            (job_id, language, total),
        )


def update_status(job_id: str, status: str) -> None:
    with _connect() as conn:
        conn.execute(
            'UPDATE sentiment_jobs SET status = %s WHERE id = %s', (status, job_id)
        )


def append_result(
    job_id: str, text: str, scores: dict[str, float], processed: int
) -> None:
    with _connect() as conn:
        conn.execute(
            'UPDATE sentiment_jobs SET results = results || %s::jsonb, processed = %s '
            'WHERE id = %s',
            (json.dumps({text: scores}), processed, job_id),
        )


def fetch_job(job_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            'SELECT id, language, total, processed, status, results '
            'FROM sentiment_jobs WHERE id = %s',
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            'id': row[0],
            'language': row[1],
            'total': row[2],
            'processed': row[3],
            'status': row[4],
            'results': row[5],
        }

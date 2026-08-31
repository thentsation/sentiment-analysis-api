import threading
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

import db
from observability.metrics import BATCH_JOBS_TOTAL

if TYPE_CHECKING:
    from services.sentiment_service import SentimentService

Language = Literal['en', 'pt']


@dataclass
class Job:
    id: str
    language: Language
    total: int
    processed: int = 0
    status: str = 'pending'
    results: dict[str, dict[str, float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add_result(self, text: str, scores: dict[str, float]) -> None:
        with self._lock:
            self.results[text] = scores
            self.processed += 1


class JobStore:
    """In-memory job store, optionally mirrored to Postgres.

    When `database_url` is set, every mutation is also persisted, and `get()`
    falls back to the database for jobs no longer held in memory (e.g. after
    a restart) — so job history survives beyond the process lifetime.
    """

    def __init__(self, maxsize: int = 100, database_url: str = '') -> None:
        self._maxsize = maxsize
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._persistent = bool(database_url)
        if self._persistent:
            db.init_db()

    def create(self, total: int, language: Language) -> Job:
        job = Job(id=uuid.uuid4().hex, language=language, total=total)
        with self._lock:
            self._jobs[job.id] = job
            while len(self._jobs) > self._maxsize:
                oldest_id = next(iter(self._jobs))
                del self._jobs[oldest_id]
        if self._persistent:
            db.insert_job(job.id, language, total)
        BATCH_JOBS_TOTAL.labels(status='accepted').inc()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is not None:
            return job
        if not self._persistent:
            return None

        row = db.fetch_job(job_id)
        if row is None:
            return None
        job = Job(
            id=row['id'],
            language=row['language'],
            total=row['total'],
            processed=row['processed'],
            status=row['status'],
            results=row['results'] or {},
        )
        with self._lock:
            self._jobs[job.id] = job
        return job

    def start(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is not None:
            job.status = 'processing'
            if self._persistent:
                db.update_status(job_id, 'processing')

    def add_result(self, job_id: str, text: str, scores: dict[str, float]) -> None:
        job = self.get(job_id)
        if job is None:
            return
        job.add_result(text, scores)
        if self._persistent:
            db.append_result(job_id, text, scores, job.processed)

    def complete(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is not None:
            job.status = 'completed'
            if self._persistent:
                db.update_status(job_id, 'completed')
            BATCH_JOBS_TOTAL.labels(status='completed').inc()

    def fail(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is not None:
            job.status = 'failed'
            if self._persistent:
                db.update_status(job_id, 'failed')
            BATCH_JOBS_TOTAL.labels(status='failed').inc()


def process_job(
    store: JobStore,
    service: 'SentimentService',
    job_id: str,
    texts: list[str],
    language: Language,
) -> None:
    store.start(job_id)
    job = store.get(job_id)
    if job is None:
        return
    try:
        for text in texts:
            scores = service.analyze_sentiment(text, language)
            store.add_result(job_id, text, scores)
    except Exception:  # noqa: BLE001
        store.fail(job_id)
        return
    store.complete(job_id)

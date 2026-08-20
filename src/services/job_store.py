import threading
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

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
    def __init__(self, maxsize: int = 100) -> None:
        self._maxsize = maxsize
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, total: int, language: Language) -> Job:
        job = Job(id=uuid.uuid4().hex, language=language, total=total)
        with self._lock:
            self._jobs[job.id] = job
            while len(self._jobs) > self._maxsize:
                oldest_id = next(iter(self._jobs))
                del self._jobs[oldest_id]
        BATCH_JOBS_TOTAL.labels(status='accepted').inc()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def start(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is not None:
            job.status = 'processing'

    def complete(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is not None:
            job.status = 'completed'
            BATCH_JOBS_TOTAL.labels(status='completed').inc()

    def fail(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is not None:
            job.status = 'failed'
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
            job.add_result(text, scores)
    except Exception:  # noqa: BLE001
        store.fail(job_id)
        return
    store.complete(job_id)

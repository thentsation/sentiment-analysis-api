from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total number of HTTP requests.',
    ['method', 'path', 'status'],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds.',
    ['method', 'path'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
SENTIMENT_ANALYSIS_TOTAL = Counter(
    'sentiment_analysis_total',
    'Total number of sentiment analyses by language and classification.',
    ['language', 'sentiment'],
)
CACHE_HITS_TOTAL = Counter('cache_hits_total', 'Total number of sentiment cache hits.')
CACHE_MISSES_TOTAL = Counter(
    'cache_misses_total', 'Total number of sentiment cache misses.'
)
CACHE_SIZE = Gauge('cache_size', 'Number of entries in the sentiment cache.')
BATCH_JOBS_TOTAL = Counter(
    'batch_jobs_total',
    'Total number of batch jobs by status.',
    ['status'],
)

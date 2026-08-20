"""Benchmark: análise com cache hit vs cache miss.

Uso (com a API rodando e rate limit alto):

    make run RATE_LIMIT_PER_MINUTE=1000000  # ou export RATE_LIMIT_PER_MINUTE=1000000
    make benchmark
"""

import random
import uuid

from locust import HttpUser, task

TEXTS = [
    'I love this product, it is absolutely amazing!',
    'This is terrible, I hate it so much.',
    'The package arrived on Tuesday morning.',
    'What a wonderful experience, thank you!',
    'The service was awful and slow.',
    'The report was delivered yesterday.',
    'Such a beautiful day, everything is great!',
    'I regret buying this, it broke immediately.',
    'The meeting is scheduled for noon.',
    'Fantastic support team, very helpful!',
]


class CacheHitUser(HttpUser):
    """Envia sempre textos do pool fixo — depois do warmup, toda análise é cache hit."""

    @task
    def analyze_cache_hit(self) -> None:
        self.client.post(
            '/v1/analyze', json={'text': random.choice(TEXTS), 'language': 'en'}
        )


class CacheMissUser(HttpUser):
    """Envia textos únicos (uuid) — toda análise executa o analyzer e popula o cache."""

    @task
    def analyze_cache_miss(self) -> None:
        text = f'I love this product! {uuid.uuid4().hex}'
        self.client.post('/v1/analyze', json={'text': text, 'language': 'en'})


TEXTS_PT = [
    'Eu amo esse produto, é maravilhoso!',
    'Que horror, é péssimo.',
    'A reunião está marcada para o meio-dia.',
    'Que experiência incrível, obrigado!',
    'O atendimento foi ótimo e rápido.',
]


class PtCacheMissUser(HttpUser):
    """Textos únicos em português — exercita o analyzer LeIA (cache miss)."""

    @task
    def analyze_pt_cache_miss(self) -> None:
        text = f'{random.choice(TEXTS_PT)} {uuid.uuid4().hex}'
        self.client.post('/v1/analyze', json={'text': text, 'language': 'pt'})

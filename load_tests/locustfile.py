import random

from locust import HttpUser, between, task

TEXTS_EN = [
    'I love this product!',
    'This is terrible...',
    'The meeting is at noon.',
    'What a wonderful day!',
    'I hate waiting in line.',
    'The report was delivered yesterday.',
]

TEXTS_PT = [
    'Eu amo isso, é maravilhoso!',
    'Que horror, é terrível!',
    'Isso é uma mesa.',
    'Que dia incrível!',
    'Odeio esperar na fila.',
    'O relatório foi entregue ontem.',
]


class SentimentApiUser(HttpUser):
    wait_time = between(0.05, 0.3)

    @task(5)
    def analyze(self) -> None:
        language = random.choice(['en', 'pt'])
        text = random.choice(TEXTS_EN if language == 'en' else TEXTS_PT)
        self.client.post('/v1/analyze', json={'text': text, 'language': language})

    @task(2)
    def analyze_multiple(self) -> None:
        self.client.post(
            '/v1/analyze_multiple',
            json={'texts': random.sample(TEXTS_EN, 3), 'language': 'en'},
        )

    @task(1)
    def analyze_statistics(self) -> None:
        self.client.post(
            '/v1/analyze_statistics', json={'texts': TEXTS_PT, 'language': 'pt'}
        )

    @task(1)
    def sentiment_classes(self) -> None:
        self.client.get('/v1/sentiment_classes')

    @task(1)
    def health(self) -> None:
        self.client.get('/health')

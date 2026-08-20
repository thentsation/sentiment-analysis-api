from repositories.sentiment_repository import analyze_sentiment
from services.cache_service import SentimentCache


def classify_compound(compound: float) -> str:
    if compound > 0.05:
        return 'positive'
    if compound < -0.05:
        return 'negative'
    return 'neutral'


class SentimentService:
    def __init__(self, cache: SentimentCache | None = None) -> None:
        self._cache = cache

    def analyze_sentiment(self, text: str, language: str = 'en') -> dict[str, float]:
        if self._cache is not None:
            cached = self._cache.get(text, language)
            if cached is not None:
                return cached

        result = analyze_sentiment(text, language)

        if self._cache is not None:
            self._cache.set(text, language, result)
        return result

    def analyze_multiple_sentiments(
        self, texts: list[str], language: str = 'en'
    ) -> dict[str, dict[str, float]]:
        return {text: self.analyze_sentiment(text, language) for text in texts}

    def analyze_statistics(
        self, texts: list[str], language: str = 'en'
    ) -> dict[str, int]:
        total_sentiment = {'positive': 0, 'neutral': 0, 'negative': 0}
        for text in texts:
            score = self.analyze_sentiment(text, language)
            total_sentiment[classify_compound(score['compound'])] += 1
        return total_sentiment


from repositories.sentiment_repository import analyze_sentiment
from typing import Dict

class SentimentService:
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        return analyze_sentiment(text)

    def analyze_multiple_sentiments(self, texts: list) -> Dict[str, Dict[str, float]]:
        results = {text: self.analyze_sentiment(text) for text in texts}
        return results

    def analyze_statistics(self, texts: list) -> Dict[str, int]:
        total_sentiment = {'positive': 0, 'neutral': 0, 'negative': 0}
        for text in texts:
            score = self.analyze_sentiment(text)
            if score['compound'] > 0.05:
                total_sentiment['positive'] += 1
            elif score['compound'] < -0.05:
                total_sentiment['negative'] += 1
            else:
                total_sentiment['neutral'] += 1
        return total_sentiment

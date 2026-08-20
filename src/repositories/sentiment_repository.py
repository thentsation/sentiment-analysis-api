from typing import Any

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer as VaderAnalyzer

from vendor.leia import SentimentIntensityAnalyzer as LeiaAnalyzer

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

ANALYZERS: dict[str, Any] = {
    'en': VaderAnalyzer(),
    'pt': LeiaAnalyzer(),
}


def analyze_sentiment(text: str, language: str = 'en') -> dict[str, float]:
    analyzer = ANALYZERS.get(language)
    if analyzer is None:
        raise ValueError(f'Unsupported language: {language}')
    return analyzer.polarity_scores(text)

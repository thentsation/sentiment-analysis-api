import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> dict[str, float]:
    sentiment_score = sia.polarity_scores(text)
    return sentiment_score

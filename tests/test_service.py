from unittest.mock import patch

from services.sentiment_service import SentimentService


@patch('services.sentiment_service.analyze_sentiment')
def test_analyze_sentiment_delegates_to_repository(mock_analyze):
    mock_analyze.return_value = {'compound': 0.8, 'pos': 0.7, 'neu': 0.3, 'neg': 0.0}
    service = SentimentService()

    result = service.analyze_sentiment('I love this!')

    mock_analyze.assert_called_once_with('I love this!')
    assert result == {'compound': 0.8, 'pos': 0.7, 'neu': 0.3, 'neg': 0.0}


@patch('services.sentiment_service.analyze_sentiment')
def test_analyze_multiple_sentiments_returns_result_per_text(mock_analyze):
    mock_analyze.side_effect = [
        {'compound': 0.8, 'pos': 0.7, 'neu': 0.3, 'neg': 0.0},
        {'compound': -0.6, 'pos': 0.0, 'neu': 0.4, 'neg': 0.6},
    ]
    service = SentimentService()

    result = service.analyze_multiple_sentiments(['I love this!', 'I hate this!'])

    assert result == {
        'I love this!': {'compound': 0.8, 'pos': 0.7, 'neu': 0.3, 'neg': 0.0},
        'I hate this!': {'compound': -0.6, 'pos': 0.0, 'neu': 0.4, 'neg': 0.6},
    }
    assert mock_analyze.call_count == 2


@patch('services.sentiment_service.analyze_sentiment')
def test_analyze_statistics_classifies_texts(mock_analyze):
    mock_analyze.side_effect = [
        {'compound': 0.8, 'pos': 0.7, 'neu': 0.3, 'neg': 0.0},
        {'compound': -0.6, 'pos': 0.0, 'neu': 0.4, 'neg': 0.6},
        {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0},
    ]
    service = SentimentService()

    result = service.analyze_statistics(['I love this!', 'I hate this!', 'This is a table.'])

    assert result == {'positive': 1, 'neutral': 1, 'negative': 1}


@patch('services.sentiment_service.analyze_sentiment')
def test_analyze_statistics_boundaries_count_as_neutral(mock_analyze):
    mock_analyze.side_effect = [
        {'compound': 0.05, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0},
        {'compound': -0.05, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0},
    ]
    service = SentimentService()

    result = service.analyze_statistics(['ok', 'ok'])

    assert result == {'positive': 0, 'neutral': 2, 'negative': 0}


@patch('services.sentiment_service.analyze_sentiment')
def test_analyze_statistics_empty_list(mock_analyze):
    service = SentimentService()

    result = service.analyze_statistics([])

    assert result == {'positive': 0, 'neutral': 0, 'negative': 0}
    mock_analyze.assert_not_called()

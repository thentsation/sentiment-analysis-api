from repositories.sentiment_repository import analyze_sentiment


def test_analyze_sentiment_returns_all_scores():
    result = analyze_sentiment('I love this!')

    assert set(result.keys()) == {'compound', 'pos', 'neu', 'neg'}


def test_analyze_sentiment_positive_text():
    result = analyze_sentiment('I love this! It is amazing and wonderful!')

    assert result['compound'] > 0
    assert result['pos'] > 0
    assert result['neg'] == 0
    assert result['neu'] >= 0


def test_analyze_sentiment_negative_text():
    result = analyze_sentiment('I hate this! It is terrible and awful!')

    assert result['compound'] < 0
    assert result['neg'] > 0
    assert result['pos'] == 0
    assert result['neu'] >= 0


def test_analyze_sentiment_neutral_text():
    result = analyze_sentiment('This is a table.')

    assert result['compound'] == 0
    assert result['pos'] == 0
    assert result['neg'] == 0
    assert result['neu'] == 1


def test_analyze_sentiment_scores_sum_to_one():
    result = analyze_sentiment('I love this! It is amazing and wonderful!')

    assert result['pos'] + result['neu'] + result['neg'] == 1

from services.cache_service import SentimentCache


def test_get_missing_entry_returns_none():
    cache = SentimentCache()

    assert cache.get('hello', 'en') is None


def test_set_then_get_returns_value():
    cache = SentimentCache(ttl=60)
    value = {'compound': 0.8, 'pos': 0.7, 'neu': 0.3, 'neg': 0.0}

    cache.set('hello', 'en', value)

    assert cache.get('hello', 'en') == value


def test_expired_entry_returns_none():
    cache = SentimentCache(ttl=0)
    cache.set('hello', 'en', {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0})

    assert cache.get('hello', 'en') is None
    assert cache.size == 0


def test_entries_are_keyed_by_language():
    cache = SentimentCache(ttl=60)
    en_value = {'compound': 0.8, 'pos': 0.7, 'neu': 0.3, 'neg': 0.0}
    pt_value = {'compound': -0.6, 'pos': 0.0, 'neu': 0.4, 'neg': 0.6}

    cache.set('oi', 'en', en_value)
    cache.set('oi', 'pt', pt_value)

    assert cache.get('oi', 'en') == en_value
    assert cache.get('oi', 'pt') == pt_value


def test_maxsize_evicts_oldest_entry():
    cache = SentimentCache(maxsize=1, ttl=60)
    value = {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}

    cache.set('first', 'en', value)
    cache.set('second', 'en', value)

    assert cache.get('first', 'en') is None
    assert cache.get('second', 'en') == value


def test_clear_returns_number_of_entries():
    cache = SentimentCache(ttl=60)
    value = {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}
    cache.set('a', 'en', value)
    cache.set('b', 'en', value)

    cleared = cache.clear()

    assert cleared == 2
    assert cache.size == 0

from web_poet.page_inputs import Stats
from web_poet.page_inputs.stats import DictStatCollector, DummyStatCollector


def test_stats_writes_to_dummy_collector():
    stats = Stats()
    stats.set("a", "1")
    stats.set("b", 2)
    stats.inc("b")
    stats.inc("b", 5)
    stats.inc("c")

    assert isinstance(stats._stats, DummyStatCollector)
    assert stats._stats._stats == {"a": "1", "b": 8, "c": 1}


def test_dict_stat_collector_data_returns_dict():
    collector = DictStatCollector()
    collector.set("latest", "ok")
    collector.inc("hits")
    collector.inc("hits", 2)
    assert isinstance(collector.data, dict)
    assert collector.data == {"latest": "ok", "hits": 3}

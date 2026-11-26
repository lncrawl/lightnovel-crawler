from types import SimpleNamespace
from unittest.mock import Mock

import scraper as scraper_lib

from lncrawl.config import Config
from lncrawl.context import ctx
from lncrawl.services.scraper import ScraperService
from lncrawl.utils.proxy_tools import ProxyExit, ProxyKind


class FakeState:
    def __init__(self, exits):
        self.exits = SimpleNamespace(release_all=Mock())
        self.configured_exits = exits


def proxy(url, label):
    return ProxyExit(url=url, label=label, kind=ProxyKind.isp)


def test_additive_save_preserves_assignments_and_uses_new_proxy(monkeypatch):
    config = Config()
    config.crawler.enable_proxy = True
    config.crawler.spread_across_exits = True
    config.crawler.proxies = [proxy("http://proxy-a.test:8000", "a"), proxy("http://proxy-b.test:8000", "b")]
    config.save = Mock()
    monkeypatch.setattr(ctx, "config", config)

    service = ScraperService()
    spawned = []

    def spawn(rotation):
        state = FakeState(rotation)
        spawned.append(state)
        return state

    monkeypatch.setattr(service, "_spawn", spawn)
    before = service.states()
    # Consumer-visible assignment: sessions draw states round-robin.
    made = []
    monkeypatch.setattr(scraper_lib, "Scraper", lambda **kwargs: made.append(kwargs) or SimpleNamespace(**kwargs))
    old_sessions = [service._session("https://one.test", 0, object()), service._session("https://two.test", 0, object())]
    old_assignments = [session.state for session in old_sessions]
    assert old_assignments == before

    service.proxies = lambda: []
    result = service.set_proxies(config.crawler.proxies + [proxy("http://proxy-c.test:8000", "c")])

    assert result == []
    assert config.save.call_count == 1
    assert service.states()[:2] == before
    new_session = service._session("https://three.test", 0, object())
    assert new_session.state is spawned[-1]
    assert new_session.state not in old_assignments
    assert [session.state for session in old_sessions] == old_assignments

import pytest
import time
from scrapy.http import Request, Response
from scrapy.spiders import Spider

from ps_helper.middlewares.proxy_rotator import (
    SequentialProxyRotatorMiddleware,
    SmartProxyRotatorMiddleware,
)


class DummySpider(Spider):
    name = "dummy"


def make_request(url="http://example.com", callback=None):
    return Request(url=url, callback=callback or (lambda r: None))


def make_response(request, status=200):
    return Response(url=request.url, request=request, status=status)


def make_exception(exc):
    return exc


@pytest.fixture
def providers():
    return {
        "p1": {"user": "u1", "password": "p1", "url": "127.0.0.1", "port": "1111"},
        "p2": {"user": "u2", "password": "p2", "url": "127.0.0.1", "port": "2222"},
    }


def test_sequential_rotation_records_stats(providers):
    middleware = SequentialProxyRotatorMiddleware(providers)
    spider = DummySpider()
    # simulate 4 requests, two proxies round-robin
    r1 = make_request("http://a")
    middleware.process_request(r1, spider)
    assert "proxy" in r1.meta

    r2 = make_request("http://b")
    middleware.process_request(r2, spider)
    assert "proxy" in r2.meta
    # simulate success for r1, failure for r2
    res1 = make_response(r1, status=200)
    middleware.process_response(r1, res1, spider)
    res2 = make_response(r2, status=500)
    middleware.process_response(r2, res2, spider)
    # check stats recorded
    stats = middleware.proxy_stats
    total_requests = sum(s["requests"] for s in stats.values())
    assert total_requests == 2
    # one success, one failure total
    total_success = sum(s["success"] for s in stats.values())
    total_fails = sum(s["fails"] for s in stats.values())
    assert total_success + total_fails == 2


def test_smart_rotation_bans_after_threshold(providers):
    """Test that proxies are banned after reaching the failure threshold and become available again after cooldown."""
    middleware = SmartProxyRotatorMiddleware(
        providers, ban_threshold=2, cooldown_time=1, rotation_mode="round_robin"
    )
    spider = DummySpider()

    # Force enough failures to trigger a ban
    for i in range(4):
        req = make_request(f"http://item/{i}")
        middleware.process_request(req, spider)
        middleware.process_exception(req, Exception("connection error"), spider)

    # At least one proxy should be temporarily banned
    banned = [p for p, s in middleware.proxy_stats.items() if s["banned_until"] > time.time()]
    assert len(banned) >= 1, "At least one proxy should be temporarily banned"

    # Wait for cooldown to expire
    time.sleep(1.1)

    # All proxies should be available again
    available = middleware.get_available_proxies()
    assert len(available) == len(middleware.proxies), "All proxies should be available after cooldown"


def test_smart_rotation_round_robin_skips_banned(providers):
    """Test that the round-robin mode skips banned proxies."""
    middleware = SmartProxyRotatorMiddleware(
        providers, ban_threshold=1, cooldown_time=5, rotation_mode="round_robin"
    )
    spider = DummySpider()

    # Force one proxy to be banned
    req = make_request("http://test")
    middleware.process_request(req, spider)
    proxy_used = req.meta["proxy"]
    middleware.register_failure(proxy_used)
    middleware._record_failure(proxy_used)

    assert middleware.proxy_stats[proxy_used]["banned_until"] > time.time()

    # The next proxy in round-robin mode should skip the banned one
    next_proxy = middleware.get_next_proxy()
    assert next_proxy != proxy_used, "Round-robin mode should skip currently banned proxies"


def test_smart_rotation_random_mode(providers):
    """Test that random mode picks proxies randomly from the list."""
    middleware = SmartProxyRotatorMiddleware(
        providers, ban_threshold=2, cooldown_time=2, rotation_mode="random"
    )
    spider = DummySpider()

    used = set()
    for i in range(5):
        req = make_request(f"http://random/{i}")
        middleware.process_request(req, spider)
        used.add(req.meta["proxy"])

    assert all(u in middleware.proxies for u in used), "All used proxies must be from the configured list"
    assert len(used) <= len(providers), "Random mode must not generate unknown proxies"

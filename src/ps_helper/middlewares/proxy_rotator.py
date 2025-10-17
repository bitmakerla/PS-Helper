import random
import logging
import time
from scrapy import signals
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)


class BaseProxyRotator:
    """Base class with shared proxy setup logic and stats."""

    def __init__(self, proxy_providers):
        self.proxy_providers = proxy_providers
        self.proxies = self._build_proxy_list(proxy_providers)
        self.proxy_stats = {
            proxy: {"requests": 0, "success": 0, "fails": 0, "banned_until": 0}
            for proxy in self.proxies
        }
        logger.info(f"ProxyRotator initialized with {len(self.proxies)} proxies")

    def _build_proxy_list(self, providers_dict):
        proxies = []
        for provider, data in providers_dict.items():
            user = data.get("user")
            password = data.get("password")
            url = data.get("url")
            port = data.get("port")
            if user and password:
                proxy = f"http://{user}:{password}@{url}:{port}"
            else:
                proxy = f"http://{url}:{port}"
            proxies.append(proxy)
        return proxies

    def _record_success(self, proxy):
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]["success"] += 1

    def _record_failure(self, proxy):
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]["fails"] += 1

    def _record_request(self, proxy):
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]["requests"] += 1

    def log_summary(self, spider):
        logger.info("=" * 60)
        logger.info("PROXY USAGE SUMMARY")
        logger.info("=" * 60)
        for proxy, stats in self.proxy_stats.items():
            total = stats["requests"]
            fails = stats["fails"]
            success = stats["success"]
            rate = (success / total * 100) if total else 0
            banned = "YES" if stats.get("banned_until", 0) > time.time() else "NO"
            spider.logger.info(
                f"Proxy: {proxy}\n"
                f"  Total requests: {total}\n"
                f"  Successes: {success}\n"
                f"  Failures: {fails}\n"
                f"  Success rate: {rate:.1f}%\n"
                f"  Banned: {banned}\n"
                f"{'-' * 50}"
            )
        logger.info("=" * 60)


class SequentialProxyRotatorMiddleware(BaseProxyRotator):
    """
    Simple sequential rotation (round-robin) with stats.
    to DOWNLOADER_MIDDLEWARES option::

        DOWNLOADER_MIDDLEWARES = {
            # ...
            'ps_helper.middlewares.proxy_rotator.SequentialProxyRotatorMiddleware': 620,
            # ...
        }

    Settings:
    * ``PROXY_PROVIDERS``  - a list of proxies to choose from;
    """

    def __init__(self, proxy_providers):
        super().__init__(proxy_providers)
        self.current_index = 0

    @classmethod
    def from_crawler(cls, crawler):
        providers = crawler.settings.get("PROXY_PROVIDERS")
        if not providers:
            raise NotConfigured("PROXY_PROVIDERS not configured")

        middleware = cls(providers)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def get_next_proxy(self):
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

    def process_request(self, request, spider):
        proxy = self.get_next_proxy()
        request.meta["proxy"] = proxy
        self._record_request(proxy)
        logger.debug(f"[Sequential] Using proxy: {proxy}")
        return None

    def process_response(self, request, response, spider):
        proxy = request.meta.get("proxy")
        if proxy:
            if response.status < 400:
                self._record_success(proxy)
            else:
                self._record_failure(proxy)
        return response

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get("proxy")
        if proxy:
            self._record_failure(proxy)
            logger.warning(f"[Sequential] Proxy {proxy} exception: {exception}")
        return None

    def spider_closed(self, spider):
        self.log_summary(spider)


class SmartProxyRotatorMiddleware(BaseProxyRotator):
    """
    Advanced rotation with failure tracking, cooldown bans, and stats.

    To enable it, add it to DOWNLOADER_MIDDLEWARES option::

        DOWNLOADER_MIDDLEWARES = {
            # ...
            'ps_helper.middlewares.proxy_rotator.SmartProxyRotatorMiddleware': 620,
            # ...
        }

    Settings:
    * ``PROXY_PROVIDERS``  - a list of proxies to choose from
    * ``PROXY_BAN_THRESHOLD``  - number of failures before the proxy is banned
    * ``PROXY_COOLDOWN``  - seconds that the proxy is deactivated
    * ``PROXY_ROTATION_MODE`` - 'random' or 'round_robin'
    """

    def __init__(
        self,
        proxy_providers,
        ban_threshold=3,
        cooldown_time=300,
        rotation_mode="random",
    ):
        super().__init__(proxy_providers)
        self.ban_threshold = ban_threshold
        self.cooldown_time = cooldown_time
        self.rotation_mode = rotation_mode
        self.current_index = 0  # for round robin

    @classmethod
    def from_crawler(cls, crawler):
        providers = crawler.settings.get("PROXY_PROVIDERS")
        if not providers:
            raise NotConfigured("PROXY_PROVIDERS not configured")

        ban_threshold = crawler.settings.getint("PROXY_BAN_THRESHOLD", 3)
        cooldown_time = crawler.settings.getint("PROXY_COOLDOWN", 300)
        rotation_mode = crawler.settings.get("PROXY_ROTATION_MODE", "random")

        middleware = cls(providers, ban_threshold, cooldown_time, rotation_mode)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def get_available_proxies(self):
        """Return only proxies not currently banned."""
        now = time.time()
        return [p for p, s in self.proxy_stats.items() if s["banned_until"] < now]

    def get_next_proxy(self):
        available = self.get_available_proxies()

        if not available:
            logger.warning("[Smart] All proxies are banned! Resetting bans.")
            for s in self.proxy_stats.values():
                s["banned_until"] = 0
            available = self.proxies

        if self.rotation_mode == "round_robin":
            # Skip banned ones but keep round-robin order
            for _ in range(len(self.proxies)):
                proxy = self.proxies[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.proxies)
                if proxy in available:
                    return proxy
            # fallback if somehow none available
            return random.choice(available)
        else:
            return random.choice(available)

    def _ban_proxy(self, proxy):
        stats = self.proxy_stats[proxy]
        stats["banned_until"] = time.time() + self.cooldown_time
        logger.info(f"[Smart] Proxy temporarily banned: {proxy}")

    def register_failure(self, proxy):
        stats = self.proxy_stats[proxy]
        stats["fails"] += 1
        if stats["fails"] >= self.ban_threshold:
            self._ban_proxy(proxy)
            stats["fails"] = 0  # reset after ban

    def process_request(self, request, spider):
        proxy = self.get_next_proxy()
        request.meta["proxy"] = proxy
        self._record_request(proxy)
        logger.debug(f"[Smart] Using proxy: {proxy}")

    def process_response(self, request, response, spider):
        proxy = request.meta.get("proxy")
        if proxy:
            if response.status >= 400:
                self.register_failure(proxy)
                self._record_failure(proxy)
                logger.warning(f"[Smart] Proxy {proxy} failed (HTTP {response.status})")
            else:
                self._record_success(proxy)
        return response

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get("proxy")
        if proxy:
            self.register_failure(proxy)
            self._record_failure(proxy)
            logger.warning(f"[Smart] Proxy {proxy} raised exception: {exception}")
        return None

    def spider_closed(self, spider):
        self.log_summary(spider)

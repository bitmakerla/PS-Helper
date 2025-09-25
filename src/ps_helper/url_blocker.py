import logging
from scrapy.exceptions import IgnoreRequest
from scrapy import signals

logger = logging.getLogger(__name__)


class URLBlockerMiddleware:
    def __init__(self, words=None, mode='partial', case_sensitive=False, log_blocked=True):
        self.blocked_words = words or []
        self.mode = mode.lower()
        self.case_sensitive = case_sensitive
        self.log_blocked = log_blocked

        self.blocked_count = 0
        self.total_count = 0

        if not self.case_sensitive:
            self.search_words = [word.lower() for word in self.blocked_words]
        else:
            self.search_words = self.blocked_words

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        instance = cls(
            words=settings.getlist('URL_BLOCKER_WORDS', []),
            mode=settings.get('URL_BLOCKER_MODE', 'partial'),
            case_sensitive=settings.getbool('URL_BLOCKER_CASE_SENSITIVE', False),
            log_blocked=settings.getbool('URL_BLOCKER_LOG_BLOCKED', True)
        )

        crawler.signals.connect(instance.spider_closed, signal=signals.spider_closed)

        return instance

    def process_request(self, request, spider):
        if not self.blocked_words:
            return None

        self.total_count += 1
        url = request.url

        search_url = url if self.case_sensitive else url.lower()

        should_block = False

        if self.mode == 'partial':
            should_block = any(word in search_url for word in self.search_words)

        if should_block:
            return self._block_request(request)

        return None

    def _block_request(self, request):
        """Bloquea la request."""
        self.blocked_count += 1

        if self.log_blocked:
            logger.info(f"🚫 URL bloqueada ({self.mode}): {request.url}")

        raise IgnoreRequest(f"URL blocked by URLBlockerMiddleware ({self.mode} mode)")

    def spider_closed(self, spider):
        """Muestra estadísticas al cerrar el spider."""
        if self.total_count > 0:
            percentage = (self.blocked_count / self.total_count) * 100
            logger.info(f"📊 URLBlockerMiddleware: {self.blocked_count}/{self.total_count} "
                        f"URLs bloqueadas ({percentage:.1f}%)")


URLBlocker = URLBlockerMiddleware

import logging
from scrapy.exceptions import IgnoreRequest
from scrapy import signals
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class URLBlockerMiddleware:
    """
    Middleware to block URLs containing specific words.
    Modes:
    - partial: Blocks if URL contains ANY word as substring
    - strict: Blocks only if words match exactly as separate components
    """

    def __init__(self, words=None, mode='partial', case_sensitive=False, log_blocked=True):
        self.blocked_words = words or []
        self.mode = mode.lower()
        self.case_sensitive = case_sensitive
        self.log_blocked = log_blocked

        if self.mode not in ['partial', 'strict']:
            logger.warning(f"Invalid mode '{self.mode}'. Using 'partial'")
            self.mode = 'partial'

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
        matched_word = None

        if self.mode == 'partial':
            for word in self.search_words:
                if word in search_url:
                    should_block = True
                    matched_word = self.blocked_words[self.search_words.index(word)]
                    break

        elif self.mode == 'strict':
            should_block, matched_word = self._strict_match(search_url)

        if should_block:
            return self._block_request(request, matched_word)

        return None

    def _strict_match(self, url):
        """Check for strict word matches in URL components"""

        parsed = urlparse(url)
        components = []

        if parsed.netloc:
            components.extend(parsed.netloc.split('.'))

        if parsed.path:
            path_segments = [seg for seg in parsed.path.split('/') if seg]
            components.extend(path_segments)

        if parsed.query:
            query_parts = [part.split('=')[0] for part in parsed.query.split('&')]
            components.extend(query_parts)

        if parsed.fragment:
            components.append(parsed.fragment)

        search_components = [comp.lower() if not self.case_sensitive else comp for comp in components]

        for word in self.search_words:
            if word in search_components:
                original_word = self.blocked_words[self.search_words.index(word)]
                return True, original_word

            for component in search_components:
                if word.startswith('.') and component.endswith(word):
                    original_word = self.blocked_words[self.search_words.index(word)]
                    return True, original_word

                if word.endswith('/') and component == word.rstrip('/'):
                    original_word = self.blocked_words[self.search_words.index(word)]
                    return True, original_word

        return False, None

    def _block_request(self, request, matched_word=None):
        self.blocked_count += 1

        if self.log_blocked:
            word_info = f" [{matched_word}]" if matched_word else ""
            logger.info(f"URL blocked ({self.mode}){word_info}: {request.url}")

        raise IgnoreRequest(f"URL blocked by URLBlockerMiddleware ({self.mode} mode)")

    def spider_closed(self, spider):
        """Show statistics when spider closes."""
        if self.total_count > 0:
            percentage = (self.blocked_count / self.total_count) * 100
            logger.info(f"📊 URLBlockerMiddleware: {self.blocked_count}/{self.total_count} "
                        f"URLs blocked ({percentage:.1f}%)")


URLBlocker = URLBlockerMiddleware

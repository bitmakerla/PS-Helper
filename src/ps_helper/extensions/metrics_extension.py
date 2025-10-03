import os
import time
import json
import math
import datetime
from collections import defaultdict
from ..scripts.generate_report import generate_html_report
from ..scripts.utils import upload_html_to_s3

from scrapy import signals
from pydantic import ValidationError


class MetricsExtension:
    def __init__(self, stats, schema=None, unique_field=None, max_buckets=30):
        """
        Scrapy Metrics Extension.

        Args:
            stats: Scrapy Stats Collector.
            schema (BaseModel, optional): Pydantic model to validate scraped items.
            unique_field (str, optional): Field name used to detect duplicates.
        """
        self.stats = stats
        self.start_time = None
        self.http_status_counter = defaultdict(int)
        self.duplicate_items = set()

        # For schema coverage (valid vs invalid items)
        self.valid_items = 0
        self.invalid_items = 0

        # Field coverage tracking
        self.field_coverage = defaultdict(lambda: {"complete": 0, "empty": 0})

        # Timeline
        self.timeline = defaultdict(int)
        self.max_buckets = max_buckets
        self.schema = schema
        self.unique_field = unique_field

    @classmethod
    def from_crawler(cls, crawler):
        schema = getattr(crawler.spidercls, "schema", None)
        unique_field = getattr(crawler.spidercls, "unique_field", None)

        max_buckets = crawler.settings.getint("METRICS_TIMELINE_BUCKETS", 30)

        ext = cls(crawler.stats, schema=schema, unique_field=unique_field, max_buckets=max_buckets)

        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)

        return ext

    def spider_opened(self, spider):
        self.start_time = time.time()
        self.stats.set_value("custom/items_scraped", 0)
        self.stats.set_value("custom/pages_processed", 0)
        self.stats.set_value("custom/items_duplicates", 0)
        self.stats.set_value("custom/errors", 0)

    def response_received(self, response, request, spider):
        self.stats.inc_value("custom/pages_processed")
        self.http_status_counter[response.status] += 1

    def item_scraped(self, item, spider):
        self.stats.inc_value("custom/items_scraped")

        # Validate schema if provided
        if self.schema:
            try:
                self.schema(**item)
                self.valid_items += 1
            except ValidationError:
                self.invalid_items += 1

        # Track field coverage
        for field, value in item.items():
            if value is None or value == "" or value == []:
                self.field_coverage[field]["empty"] += 1
            else:
                self.field_coverage[field]["complete"] += 1

        # Temporal timeline: save timestamp in seconds
        elapsed_seconds = int(time.time() - self.start_time)
        self.timeline[elapsed_seconds] += 1

        # Check duplicates if unique_field is defined
        if self.unique_field and self.unique_field in item:
            value = item[self.unique_field]
            if value in self.duplicate_items:
                self.stats.inc_value("custom/items_duplicates")
            else:
                self.duplicate_items.add(value)

    def spider_error(self, failure, response, spider):
        self.stats.inc_value("custom/errors")

    def spider_closed(self, spider, reason):
        elapsed = time.time() - self.start_time
        total_minutes = elapsed / 60

        # Get size of the interval
        interval_size = max(1, math.ceil(total_minutes / self.max_buckets))

        # Success rate
        total_requests = self.stats.get_value("downloader/request_count", 0)
        status_200 = self.http_status_counter.get(200, 0)
        success_rate = (status_200 / total_requests * 100) if total_requests > 0 else 0

        # Group timeline
        aggregated = defaultdict(int)
        for sec, count in self.timeline.items():
            minute = sec // 60
            bucket_start = (minute // interval_size) * interval_size
            bucket_end = bucket_start + interval_size
            label = f"{bucket_start}-{bucket_end}m"
            aggregated[label] += count

        timeline_sorted = [
            {"interval": k, "items": v}
            for k, v in sorted(
                aggregated.items(),
                key=lambda x: int(x[0].split("-")[0])
            )
        ]

        items = self.stats.get_value("custom/items_scraped", 0)
        pages = self.stats.get_value("custom/pages_processed", 0)

        # Speed
        items_per_min = items / (elapsed / 60) if elapsed > 0 else 0
        pages_per_min = pages / (elapsed / 60) if elapsed > 0 else 0
        time_per_page = elapsed / pages if pages > 0 else 0

        # Schema coverage
        total_checked = self.valid_items + self.invalid_items
        schema_coverage_percentage = (
            (self.valid_items / total_checked) * 100 if total_checked else 0
        )

        # Timeouts and retries
        timeouts = self.stats.get_value(
            "downloader/exception_type_count/twisted.internet.error.TimeoutError", 0
        )
        retries_total = self.stats.get_value("retry/count", 0)

        retry_reasons = {
            k.replace("retry/reason_count/", ""): v
            for k, v in self.stats.get_stats().items()
            if k.startswith("retry/reason_count/")
        }

        # Memory and bytes
        peak_mem = self.stats.get_value("memusage/max", 0)  # bytes
        total_bytes = self.stats.get_value("downloader/response_bytes", 0)

        metrics = {
            "spider_name": spider.name,
            "reason": reason,
            "elapsed_time_seconds": round(elapsed, 2),
            "items_scraped": items,
            "pages_processed": pages,
            "items_per_minute": round(items_per_min, 2),
            "pages_per_minute": round(pages_per_min, 2),
            "time_per_page_seconds": round(time_per_page, 2),
            "success_rate": round(success_rate, 2),
            "schema_coverage": {
                "percentage": round(schema_coverage_percentage, 2),
                "valid": self.valid_items,
                "checked": total_checked,
                "fields": dict(self.field_coverage),
            },
            "http_errors": dict(self.http_status_counter),
            "duplicates": self.stats.get_value("custom/items_duplicates", 0),
            "timeouts": timeouts,
            "retries": {
                "total": retries_total,
                "by_reason": retry_reasons,
            },
            "resources": {
                "peak_memory_bytes": peak_mem,
                "downloaded_bytes": total_bytes,
            },
            "timeline": timeline_sorted,
            "timeline_interval_minutes": interval_size,
        }

        # Save metrics in folder by date
        now = datetime.datetime.now()
        day_folder = now.strftime("%Y-%m-%d")
        filename = now.strftime("metrics-%Y-%m-%d_%H-%M-%S.json")

        output_dir = os.path.join("metrics", day_folder)
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        spider.logger.info(f"Saved metrics: {file_path}")
        print(json.dumps(metrics, indent=2, ensure_ascii=False))

        if os.getenv('PRODUCTION') == 'True':
            try:
                _, html_content = generate_html_report(file_path)

                url = self._upload_report_to_s3(html_content, spider)
                spider.logger.info(f"Report uploaded to S3: {url}")

            except Exception as e:
                spider.logger.error(f"Failed to generate/upload HTML report: {e}")

    def _upload_report_to_s3(self, html_content, spider):
        """Upload HTML report to S3 from memory"""

        bucket_name = os.getenv('S3_BUCKET_NAME')

        expiration_days = int(os.getenv('REPORT_EXPIRATION_DAYS', '3'))
        expiration_seconds = expiration_days * 24 * 3600

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        key = f"scrapy-reports/{spider.name}/{timestamp}-report.html"

        url = upload_html_to_s3(
            html_str=html_content,
            bucket=bucket_name,
            key=key,
            publico=False,
            expira_seg=expiration_seconds
        )

        return url

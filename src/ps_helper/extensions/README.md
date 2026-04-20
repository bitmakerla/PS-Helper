# MetricsExtension for Scrapy

`MetricsExtension` is a custom Scrapy extension that collects detailed runtime statistics about spiders, such as scraped items, page responses, schema validation, duplicates, retries, and resource usage.

## Features

- **Item & Page Tracking**: Count scraped items and processed pages in real-time.
- **Schema Validation**: Validate scraped items against a Pydantic schema if provided.
- **Duplicate Detection**: Detect duplicate items using a unique field.
- **Field Coverage**: Track how many fields are filled vs. empty across all items.
- **Timeline Metrics**: Track scraping speed and item counts over time.
- **Success Rate**: Measure percentage of successful (HTTP 200) responses.
- **Retry & Timeout Analysis**: Record retry attempts and timeout errors.
- **Resource Monitoring**: Capture memory usage and response bytes.
- **JSON Reports**: Save structured metrics reports to `metrics/YYYY-MM-DD/` folders.
- **curl_cffi Transfer Metrics**: Reusable helper for downloaded/uploaded bytes and optional integration with `downloader/response_bytes`.

------------------------------------------------------------------------

## Installation

Place the extension in your Scrapy project and enable it in `settings.py`:

```python
EXTENSIONS = {
    'ps_helper.extensions.metrics_extension.MetricsExtension': 500,
    'ps_helper.extensions.slack_extension.SlackAlertExtension': 600,
}

SLACK_WEBHOOK_URL = 'url_here'
```

Optionally configure the number of timeline buckets:

```python
METRICS_TIMELINE_BUCKETS = 30

# If True, curl_cffi downloaded bytes are also added to downloader/response_bytes
PS_HELPER_CURL_ADD_TO_DOWNLOADER_RESPONSE_BYTES = True
```

## Example Usage

If the spider defines a schema and unique field:

```python
from pydantic import BaseModel

class ProductSchema(BaseModel):
    id: int
    name: str
    price: float

class MySpider(scrapy.Spider):
    name = "my_spider"
    schema = ProductSchema
    unique_field = "id"
```

The extension will validate items and detect duplicates automatically.

------------------------------------------------------------------------

## Reusable curl_cffi Byte Tracker

You can use this helper from any project to record transfer bytes from `curl_cffi` responses:

```python
from ps_helper.extensions import record_curl_transfer_bytes

# inside a spider or custom download handler
record_curl_transfer_bytes(
    stats=self.crawler.stats,
    curl_response=curl_resp,
    add_to_downloader_response_bytes=True,
)
```

What it records:

- `curl_cffi/bytes_down`
- `curl_cffi/bytes_up`
- `curl_cffi/bytes_total`
- `curl_cffi/response_count`
- Optional: `downloader/response_bytes` (downloaded bytes)

The helper prefers curl/libcurl transfer sizes when available and falls back to `len(response.content)`.

## TrackedCurlSession (Recommended)

For automatic tracking on every request, use `TrackedCurlSession` as a drop-in wrapper:

```python
from ps_helper.extensions import TrackedCurlSession

class MySpider(scrapy.Spider):
    name = "my_spider"

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.curl_session = TrackedCurlSession(
            stats=crawler.stats,
            add_to_downloader_response_bytes=crawler.settings.getbool(
                "PS_HELPER_CURL_ADD_TO_DOWNLOADER_RESPONSE_BYTES", True
            ),
        )
        return spider
```

Then keep using `self.curl_session.get(...)` / `post(...)` normally.

------------------------------------------------------------------------


## Metrics Report

When the spider closes, a JSON report is saved under:

```
metrics/YYYY-MM-DD/metrics-YYYY-MM-DD_HH-MM-SS.json
```

The JSON includes:

- Elapsed time
- Items and pages scraped
- Success rate
- Schema coverage
- Duplicates
- HTTP status distribution
- Retries and reasons
- Memory usage
- Timeline of items per minute

Example structure:

```json
{
  "spider_name": "my_spider",
  "reason": "finished",
  "elapsed_time_seconds": 120.5,
  "items_scraped": 50,
  "pages_processed": 20,
  "items_per_minute": 25.0,
  "pages_per_minute": 10.0,
  "success_rate": 95.5,
  "schema_coverage": {
    "percentage": 90.0,
    "valid": 45,
    "checked": 50,
    "fields": {
      "id": {"complete": 50, "empty": 0},
      "name": {"complete": 49, "empty": 1},
      "price": {"complete": 50, "empty": 0}
    }
  },
  "http_errors": {
    "200": 19,
    "404": 1
  },
  "duplicates": 2,
  "timeouts": 0,
  "retries": {
    "total": 1,
    "by_reason": {"500 Internal Server Error": 1}
  },
  "resources": {
    "peak_memory_bytes": 104857600,
    "downloaded_bytes": 5242880
  },
  "timeline": [
    {"interval": "0-1m", "items": 10},
    {"interval": "1-2m", "items": 20},
    {"interval": "2-3m", "items": 20}
  ],
  "timeline_interval_minutes": 1
}
```
------------------------------------------------------------------------

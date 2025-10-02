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

------------------------------------------------------------------------

## Installation

Place the extension in your Scrapy project and enable it in `settings.py`:

```python
EXTENSIONS = {
    'ps_helper.extensions.metrics_extension.MetricsExtension': 500,
}
```

Optionally configure the number of timeline buckets:

```python
METRICS_TIMELINE_BUCKETS = 30
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


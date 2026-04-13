# PS Helper

**PS Helper** is a Python package developed by the Professional Services team.  
It provides a set of helper libraries and command-line tools to speed up and standardize development workflows.

---

## 🚀 Features
- Ready-to-use Python utilities for internal projects.
- **Legacy SSL Fix:** Resolves `unsafe legacy renegotiation disabled` errors.
- **Proxy Rotation:** Sequential and Smart rotation middlewares with banning logic.
- **Scrapy Metrics Extension:** Deep runtime analytics and Pydantic validation.
- **Scrapy Slack Alerts:** Professional monitoring for jobs running on Estela.
- **URL Blocker Middleware:** Intelligent filtering for unwanted requests.
- **CLI Tools:** Command-line utilities for project templates and report generation.

## 📦 Installation

You can install **PS Helper** in two ways:

### Option 1: Local installation (development mode)
Clone the repository and install it with `pip`:

```bash
git clone https://github.com/bitmakerla/ps-helper.git
cd ps-helper
pip install -e .
```

This will install the package in editable mode, so any code changes will be reflected immediately.

### Option 2: Install directly from GitHub

You can install the package without cloning:

```bash
pip install git+https://github.com/bitmakerla/ps-helper.git
```

---

## 🛠 Usage
Check available commands:
```bash
ps-helper --help
```

### Create Project Template

Create a new project from the template:
```bash
ps-helper create-repo-template MyProject
```

### Generate Scrapy Reports

Generate beautiful HTML reports from Scrapy metrics JSON files:
```bash
ps-helper create-report scrapy_stats.json
```
This will automatically create a report named scrapy_stats-report.html in the same directory as your metrics file.

---

## LegacyConnectContextFactory

This middleware provides a custom `ClientContextFactory` for **Scrapy** to fix the SSL error:

`SSL routines: unsafe legacy renegotiation disabled error`


### Installation

Place the extension in your Scrapy project and enable it in `settings.py`:

```python
DOWNLOADER_CLIENTCONTEXTFACTORY = "ps_helper.middlewares.LegacyConnectContextFactory"
```
Scrapy will then use the LegacyConnectContextFactory for all HTTPS connections.

--------------------------------------

## Proxy Rotator Middlewares

This module provides two Scrapy downloader middlewares for rotating HTTP proxies with optional smart banning logic and statistics tracking.

### 🧩 Middlewares

#### **1. SequentialProxyRotatorMiddleware**
A simple **round-robin** proxy rotation strategy that cycles through proxies sequentially.

##### Enable in `settings.py`
```python
DOWNLOADER_MIDDLEWARES = {
    "ps_helper.middlewares.proxy_rotator.SequentialProxyRotatorMiddleware": 620,
}
```

##### Required Setting
```python
PROXY_PROVIDERS = {
    "provider1": {"url": "proxy1.com", "port": 8080},
    "provider2": {"url": "proxy2.com", "port": 8080, "user": "user", "password": "pass"},
}
```

##### Behavior
- Rotates proxies in order.  
- Logs total requests, successes, failures, and success rate for each proxy when the spider closes.

#### **2. SmartProxyRotatorMiddleware**
A more advanced rotation system that supports banning failed proxies temporarily and two rotation modes (`random` or `round_robin`).

##### Enable in `settings.py`
```python
DOWNLOADER_MIDDLEWARES = {
    "ps_helper.middlewares.proxy_rotator.SmartProxyRotatorMiddleware": 620,
}
```

##### Available Settings
```python
PROXY_PROVIDERS = {
    "proxy1": {"url": "proxy1.com", "port": 8080},
    "proxy2": {"url": "proxy2.com", "port": 8080, "user": "user", "password": "pass"},
}

PROXY_BAN_THRESHOLD = 3     # Number of failures before banning a proxy
PROXY_COOLDOWN = 300        # Cooldown duration in seconds for banned proxies
PROXY_ROTATION_MODE = "random"  # 'random' or 'round_robin'
```

##### Features
- Automatically bans proxies that fail too many times.
- Supports **cooldown** (temporary ban).
- Chooses proxies randomly or sequentially while skipping banned ones.
- Displays a detailed summary when the spider closes.

------------------------------------------------------------------------
## 🕷️ Scrapy URL Blocker Middleware

Block unwanted URLs in your Scrapy projects with intelligent filtering.

### Quick Setup

1. **Add to your Scrapy project's `settings.py`:**
```python
"DOWNLOADER_MIDDLEWARES": {
    'ps_helper.blockers.url_blocker.URLBlockerMiddleware': 585,
},

# Configure words to block
"URL_BLOCKER_WORDS": ['admin', 'login', '.css', '.js', 'api/']
"URL_BLOCKER_MODE": 'partial'  # or 'strict'
```

2. **Run your spider** - unwanted URLs will be automatically filtered!

### Filtering Modes

#### Partial Mode (Default)
Blocks URLs containing the word as a substring:
```python
URL_BLOCKER_MODE = 'partial'
URL_BLOCKER_WORDS = ['auth']

# Results:
# ❌ BLOCKED: site.com/authentication (contains 'auth')
# ❌ BLOCKED: site.com/auth (contains 'auth')
```

#### Strict Mode
Blocks only exact word matches in URL components:
```python
URL_BLOCKER_MODE = 'strict'  
URL_BLOCKER_WORDS = ['auth']

# Results:
# ✅ ALLOWED: site.com/authentication ('auth' ≠ 'authentication')
# ❌ BLOCKED: site.com/auth ('auth' = 'auth')
```

### Configuration Options

```python
# Required
URL_BLOCKER_WORDS = ['admin', 'login', '.pdf', 'tracking']

# Optional (with defaults)
URL_BLOCKER_MODE = 'partial'           # 'partial' or 'strict'
URL_BLOCKER_CASE_SENSITIVE = False     # Case sensitivity  
URL_BLOCKER_LOG_BLOCKED = True         # Show blocked URLs in logs
```
------------------------------------------------------------------------
## MetricsExtension for Scrapy

`MetricsExtension` is a custom Scrapy extension that collects detailed runtime statistics about spiders, such as scraped items, page responses, schema validation, duplicates, retries, and resource usage.

### Features

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

### Installation

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

### Example Usage

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
## 🔔 Scrapy Slack Alerts (Estela Optimized)
Monitor your spider's health in real-time with professional Block Kit notifications.

### Key Features
* High-Signal Monitoring: Alerts only trigger when anomalies are detected (no spam for successful runs).

* KPI Dashboard: Visualizes Success Rate, HTTP Success, and Goal Achievement metrics.

* Dynamic Error Breakdown: Lists specific network codes (403, 407, 429, 50x) and Timeouts only if they occurred.

* One-Click Debugging: Includes a direct button to view the logs in the Estela platform.

### Setup
Configure settings.py:

```python
EXTENSIONS = {
    'ps_helper.extensions.slack_alerts.EstelaSlackAlerts': 500,
}
# Slack Webhook URL for the alerts channel
SLACK_WEBHOOK_URL = '[https://hooks.slack.com/services/YOUR/WEBHOOK/URL](https://hooks.slack.com/services/YOUR/WEBHOOK/URL)'
```

### (Optional) Set Target Items:
Define ITEMS_EXPECTED in your spider to track yield performance:

```python
class MySpider(scrapy.Spider):
    name = "my_spider"
    ITEMS_EXPECTED = 500  # Triggers 'Low Yield' alert if results are below this number
```
### Anomaly Triggers
The extension automatically sends a report if any of these conditions are met:

* Zero Items: No data was extracted.
* Low Yield: Scraped count is lower than ITEMS_EXPECTED.
* Abnormal Exit: Spider closed with a reason other than finished.
* High Error Rate: Log errors exceed 50% of total responses.
* Network Degradation: Cumulative proxy bans or timeouts exceed the safety threshold.
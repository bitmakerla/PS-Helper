# PS Helper

**PS Helper** is a Python package developed by the Professional Services team.  
It provides a set of helper libraries and command-line tools to speed up and standardize development workflows.

---

## 🚀 Features
- Ready-to-use Python utilities for internal projects.
- CLI commands for common tasks (e.g., creating repository templates).
- Easy to install and extend.

---

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

### Track curl_cffi Downloaded Bytes

Use the reusable helper to register transfer bytes in Scrapy stats (including `downloader/response_bytes`):

```python
from ps_helper.extensions import record_curl_transfer_bytes

record_curl_transfer_bytes(
    stats=self.crawler.stats,
    curl_response=curl_resp,
    add_to_downloader_response_bytes=True,
)
```

With `MetricsExtension`, this is also reflected in the final JSON report under `resources`.

For automatic tracking in every curl request, use `TrackedCurlSession`:

```python
from ps_helper.extensions import TrackedCurlSession

self.curl_session = TrackedCurlSession(stats=self.crawler.stats)

# keep using get/post as usual
curl_resp = self.curl_session.get(url, impersonate="chrome120")
```

---

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

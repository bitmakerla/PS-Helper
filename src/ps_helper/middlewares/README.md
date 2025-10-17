# LegacyConnectContextFactory

This middleware provides a custom `ClientContextFactory` for **Scrapy** to fix the SSL error:

`SSL routines: unsafe legacy renegotiation disabled error`

---

## Installation

Place the extension in your Scrapy project and enable it in `settings.py`:

```python
DOWNLOADER_CLIENTCONTEXTFACTORY = "ps_helper.middlewares.LegacyConnectContextFactory"
```
Scrapy will then use the LegacyConnectContextFactory for all HTTPS connections.

--------------------------------------

# Proxy Rotator Middlewares

This module provides two Scrapy downloader middlewares for rotating HTTP proxies with optional smart banning logic and statistics tracking.

---

## 🧩 Middlewares

### **1. SequentialProxyRotatorMiddleware**
A simple **round-robin** proxy rotation strategy that cycles through proxies sequentially.

#### Enable in `settings.py`
```python
DOWNLOADER_MIDDLEWARES = {
    "ps_helper.middlewares.proxy_rotator.SequentialProxyRotatorMiddleware": 620,
}
```

#### Required Setting
```python
PROXY_PROVIDERS = {
    "provider1": {"url": "proxy1.com", "port": 8080},
    "provider2": {"url": "proxy2.com", "port": 8080, "user": "user", "password": "pass"},
}
```

#### Behavior
- Rotates proxies in order.  
- Logs total requests, successes, failures, and success rate for each proxy when the spider closes.

---

### **2. SmartProxyRotatorMiddleware**
A more advanced rotation system that supports banning failed proxies temporarily and two rotation modes (`random` or `round_robin`).

#### Enable in `settings.py`
```python
DOWNLOADER_MIDDLEWARES = {
    "ps_helper.middlewares.proxy_rotator.SmartProxyRotatorMiddleware": 620,
}
```

#### Available Settings
```python
PROXY_PROVIDERS = {
    "proxy1": {"url": "proxy1.com", "port": 8080},
    "proxy2": {"url": "proxy2.com", "port": 8080, "user": "user", "password": "pass"},
}

PROXY_BAN_THRESHOLD = 3     # Number of failures before banning a proxy
PROXY_COOLDOWN = 300        # Cooldown duration in seconds for banned proxies
PROXY_ROTATION_MODE = "random"  # 'random' or 'round_robin'
```

#### Features
- Automatically bans proxies that fail too many times.
- Supports **cooldown** (temporary ban).
- Chooses proxies randomly or sequentially while skipping banned ones.
- Displays a detailed summary when the spider closes.

---

## 🧠 Summary Logs Example
When a spider finishes, a summary like this appears in the logs:

```
============================================================
PROXY USAGE SUMMARY
============================================================
Proxy: http://proxy1.com:8080
  Total requests: 120
  Successes: 110
  Failures: 10
  Success rate: 91.7%
  Banned: NO
--------------------------------------------------
Proxy: http://proxy2.com:8080
  Total requests: 50
  Successes: 25
  Failures: 25
  Success rate: 50.0%
  Banned: YES
============================================================
```

---

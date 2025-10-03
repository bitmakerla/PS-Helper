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

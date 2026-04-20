"""Helpers to record curl_cffi transfer metrics in Scrapy stats."""

from __future__ import annotations

from curl_cffi import requests as curl_requests
from curl_cffi.const import CurlInfo


class TrackedCurlSession:
    """Wrapper around curl_cffi Session that auto-records transfer bytes."""

    def __init__(
        self,
        *,
        stats,
        session=None,
        add_to_downloader_response_bytes=True,
        dedupe_on_response=True,
    ):
        self.stats = stats
        self.add_to_downloader_response_bytes = add_to_downloader_response_bytes
        self.dedupe_on_response = dedupe_on_response
        self._session = session if session is not None else self._build_default_session()

    @staticmethod
    def _build_default_session():
        return curl_requests.Session()

    def _track(self, response):
        record_curl_transfer_bytes(
            self.stats,
            response,
            add_to_downloader_response_bytes=self.add_to_downloader_response_bytes,
            dedupe_on_response=self.dedupe_on_response,
        )
        return response

    def request(self, method, url, *args, **kwargs):
        response = self._session.request(method, url, *args, **kwargs)
        return self._track(response)

    def get(self, url, *args, **kwargs):
        return self.request("GET", url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self.request("POST", url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        return self.request("PUT", url, *args, **kwargs)

    def patch(self, url, *args, **kwargs):
        return self.request("PATCH", url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        return self.request("DELETE", url, *args, **kwargs)

    def head(self, url, *args, **kwargs):
        return self.request("HEAD", url, *args, **kwargs)

    def options(self, url, *args, **kwargs):
        return self.request("OPTIONS", url, *args, **kwargs)

    def close(self):
        close_fn = getattr(self._session, "close", None)
        if callable(close_fn):
            close_fn()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def __getattr__(self, item):
        return getattr(self._session, item)


def _safe_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


def _extract_transfer_sizes(curl_response):
    """Return tuple: (down_bytes, up_bytes)."""
    download_size = 0
    upload_size = 0
    header_size = 0
    request_size = 0

    curl_handle = getattr(curl_response, "curl", None)
    if curl_handle is not None:
        try:
            download_size = _safe_int(curl_handle.getinfo(CurlInfo.SIZE_DOWNLOAD_T))
            upload_size = _safe_int(curl_handle.getinfo(CurlInfo.SIZE_UPLOAD_T))
            header_size = _safe_int(curl_handle.getinfo(CurlInfo.HEADER_SIZE))
            request_size = _safe_int(curl_handle.getinfo(CurlInfo.REQUEST_SIZE))
        except Exception:
            download_size = 0
            upload_size = 0
            header_size = 0
            request_size = 0

    if (download_size + header_size) == 0:
        download_size = len(getattr(curl_response, "content", b"") or b"")

    down_bytes = download_size + header_size
    up_bytes = request_size + upload_size
    return down_bytes, up_bytes


def record_curl_transfer_bytes(
    stats,
    curl_response,
    *,
    add_to_downloader_response_bytes=True,
    dedupe_on_response=True,
):
    """Record curl_cffi transfer metrics in Scrapy stats.

    Args:
        stats: Scrapy stats collector.
        curl_response: response object returned by curl_cffi.
        add_to_downloader_response_bytes: if True, increment
            ``downloader/response_bytes`` with downloaded bytes.
        dedupe_on_response: if True, skip if metrics were already recorded for
            this response instance.
    """
    if stats is None or curl_response is None:
        return {"down_bytes": 0, "up_bytes": 0, "total_bytes": 0}

    if dedupe_on_response and getattr(curl_response, "_ps_helper_curl_metrics_recorded", False):
        return {"down_bytes": 0, "up_bytes": 0, "total_bytes": 0}

    down_bytes, up_bytes = _extract_transfer_sizes(curl_response)
    total_bytes = down_bytes + up_bytes

    stats.inc_value("curl_cffi/bytes_down", down_bytes)
    stats.inc_value("curl_cffi/bytes_up", up_bytes)
    stats.inc_value("curl_cffi/bytes_total", total_bytes)
    stats.inc_value("curl_cffi/response_count", 1)

    if add_to_downloader_response_bytes:
        stats.inc_value("downloader/response_bytes", down_bytes)

    if dedupe_on_response:
        try:
            setattr(curl_response, "_ps_helper_curl_metrics_recorded", True)
        except Exception:
            pass

    return {
        "down_bytes": down_bytes,
        "up_bytes": up_bytes,
        "total_bytes": total_bytes,
    }

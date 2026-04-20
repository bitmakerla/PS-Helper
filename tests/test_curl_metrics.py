import sys
import types

from ps_helper.extensions.curl_metrics import (TrackedCurlSession,
                                               record_curl_transfer_bytes)


class DummyStats:
    def __init__(self):
        self._values = {}

    def inc_value(self, key, value=1):
        self._values[key] = self._values.get(key, 0) + value

    def get_value(self, key, default=0):
        return self._values.get(key, default)


class DummyCurl:
    def __init__(self, mapping):
        self.mapping = mapping

    def getinfo(self, key):
        return self.mapping.get(key, 0)


class DummyResponse:
    def __init__(self, content=b"", curl=None):
        self.content = content
        self.curl = curl


class DummySession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, *args, **kwargs):
        self.calls.append((method, url, args, kwargs))
        return self.response


def _install_fake_curlinfo(monkeypatch):
    curl_module = types.ModuleType("curl_cffi")
    const_module = types.ModuleType("curl_cffi.const")

    class CurlInfo:
        SIZE_DOWNLOAD_T = "SIZE_DOWNLOAD_T"
        SIZE_UPLOAD_T = "SIZE_UPLOAD_T"
        HEADER_SIZE = "HEADER_SIZE"
        REQUEST_SIZE = "REQUEST_SIZE"

    const_module.CurlInfo = CurlInfo
    monkeypatch.setitem(sys.modules, "curl_cffi", curl_module)
    monkeypatch.setitem(sys.modules, "curl_cffi.const", const_module)
    return CurlInfo


def test_records_bytes_from_curl_getinfo(monkeypatch):
    curl_info = _install_fake_curlinfo(monkeypatch)
    stats = DummyStats()
    curl = DummyCurl(
        {
            curl_info.SIZE_DOWNLOAD_T: 1200,
            curl_info.SIZE_UPLOAD_T: 100,
            curl_info.HEADER_SIZE: 300,
            curl_info.REQUEST_SIZE: 50,
        }
    )
    response = DummyResponse(content=b"x" * 10, curl=curl)

    result = record_curl_transfer_bytes(stats, response)

    assert result["down_bytes"] == 1500
    assert result["up_bytes"] == 150
    assert result["total_bytes"] == 1650
    assert stats.get_value("curl_cffi/bytes_down") == 1500
    assert stats.get_value("curl_cffi/bytes_up") == 150
    assert stats.get_value("curl_cffi/bytes_total") == 1650
    assert stats.get_value("curl_cffi/response_count") == 1
    assert stats.get_value("downloader/response_bytes") == 1500


def test_falls_back_to_content_length_without_curl_info(monkeypatch):
    monkeypatch.delitem(sys.modules, "curl_cffi", raising=False)
    monkeypatch.delitem(sys.modules, "curl_cffi.const", raising=False)

    stats = DummyStats()
    response = DummyResponse(content=b"abcde", curl=None)

    result = record_curl_transfer_bytes(stats, response)

    assert result["down_bytes"] == 5
    assert result["up_bytes"] == 0
    assert result["total_bytes"] == 5
    assert stats.get_value("downloader/response_bytes") == 5


def test_deduplicates_same_response_instance(monkeypatch):
    curl_info = _install_fake_curlinfo(monkeypatch)
    stats = DummyStats()
    curl = DummyCurl(
        {
            curl_info.SIZE_DOWNLOAD_T: 100,
            curl_info.SIZE_UPLOAD_T: 0,
            curl_info.HEADER_SIZE: 20,
            curl_info.REQUEST_SIZE: 10,
        }
    )
    response = DummyResponse(content=b"ignored", curl=curl)

    first = record_curl_transfer_bytes(stats, response)
    second = record_curl_transfer_bytes(stats, response)

    assert first["total_bytes"] == 130
    assert second["total_bytes"] == 0
    assert stats.get_value("curl_cffi/response_count") == 1
    assert stats.get_value("downloader/response_bytes") == 120


def test_can_skip_downloader_response_bytes(monkeypatch):
    curl_info = _install_fake_curlinfo(monkeypatch)
    stats = DummyStats()
    curl = DummyCurl(
        {
            curl_info.SIZE_DOWNLOAD_T: 200,
            curl_info.SIZE_UPLOAD_T: 10,
            curl_info.HEADER_SIZE: 40,
            curl_info.REQUEST_SIZE: 20,
        }
    )
    response = DummyResponse(content=b"", curl=curl)

    record_curl_transfer_bytes(
        stats,
        response,
        add_to_downloader_response_bytes=False,
    )

    assert stats.get_value("curl_cffi/bytes_total") == 270
    assert stats.get_value("downloader/response_bytes") == 0


def test_tracked_session_get_records_and_forwards_kwargs(monkeypatch):
    curl_info = _install_fake_curlinfo(monkeypatch)
    stats = DummyStats()
    response = DummyResponse(
        content=b"",
        curl=DummyCurl(
            {
                curl_info.SIZE_DOWNLOAD_T: 500,
                curl_info.SIZE_UPLOAD_T: 20,
                curl_info.HEADER_SIZE: 100,
                curl_info.REQUEST_SIZE: 30,
            }
        ),
    )
    session = DummySession(response)
    tracked = TrackedCurlSession(stats=stats, session=session)

    returned = tracked.get("https://example.com", impersonate="chrome120", timeout=10)

    assert returned is response
    assert session.calls[0][0] == "GET"
    assert session.calls[0][1] == "https://example.com"
    assert session.calls[0][3]["impersonate"] == "chrome120"
    assert session.calls[0][3]["timeout"] == 10
    assert stats.get_value("curl_cffi/bytes_down") == 600
    assert stats.get_value("curl_cffi/bytes_up") == 50
    assert stats.get_value("curl_cffi/bytes_total") == 650
    assert stats.get_value("downloader/response_bytes") == 600


def test_tracked_session_request_method_is_supported(monkeypatch):
    curl_info = _install_fake_curlinfo(monkeypatch)
    stats = DummyStats()
    response = DummyResponse(
        content=b"",
        curl=DummyCurl(
            {
                curl_info.SIZE_DOWNLOAD_T: 100,
                curl_info.SIZE_UPLOAD_T: 10,
                curl_info.HEADER_SIZE: 20,
                curl_info.REQUEST_SIZE: 5,
            }
        ),
    )
    session = DummySession(response)
    tracked = TrackedCurlSession(stats=stats, session=session)

    tracked.request("POST", "https://example.com/x", data={"k": "v"})

    assert session.calls[0][0] == "POST"
    assert session.calls[0][1] == "https://example.com/x"
    assert session.calls[0][3]["data"] == {"k": "v"}
    assert stats.get_value("curl_cffi/response_count") == 1


def test_tracked_session_respects_toggle_for_response_bytes(monkeypatch):
    curl_info = _install_fake_curlinfo(monkeypatch)
    stats = DummyStats()
    response = DummyResponse(
        content=b"",
        curl=DummyCurl(
            {
                curl_info.SIZE_DOWNLOAD_T: 300,
                curl_info.SIZE_UPLOAD_T: 20,
                curl_info.HEADER_SIZE: 80,
                curl_info.REQUEST_SIZE: 40,
            }
        ),
    )
    session = DummySession(response)
    tracked = TrackedCurlSession(
        stats=stats,
        session=session,
        add_to_downloader_response_bytes=False,
    )

    tracked.post("https://example.com/y")

    assert stats.get_value("curl_cffi/bytes_total") == 440
    assert stats.get_value("downloader/response_bytes") == 0

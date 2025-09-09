from __future__ import annotations

import json
from typing import Any

import pytest

from common.http import HttpClient


class DummyResponse:
    def __init__(self, status_code: int, payload: Any = None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"ok": True}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self) -> Any:
        return self._payload


def test_http_client_retries_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = HttpClient()
    calls = {"count": 0}

    def fake_request(method: str, url: str, **kwargs: Any) -> DummyResponse:  # type: ignore[override]
        calls["count"] += 1
        # First call 500, second 429, third 200
        if calls["count"] == 1:
            return DummyResponse(500)
        if calls["count"] == 2:
            return DummyResponse(429)
        return DummyResponse(200, {"ok": True})

    monkeypatch.setattr(client, "_session", type("S", (), {"request": staticmethod(fake_request)})())
    resp = client.request_with_retry("get", "http://x")
    assert resp.status_code == 200
    assert calls["count"] == 3


def test_http_client_gives_up_after_max(monkeypatch: pytest.MonkeyPatch) -> None:
    client = HttpClient()
    calls = {"count": 0}

    def fake_request(method: str, url: str, **kwargs: Any) -> DummyResponse:  # type: ignore[override]
        calls["count"] += 1
        return DummyResponse(500)

    monkeypatch.setattr(client, "_session", type("S", (), {"request": staticmethod(fake_request)})())
    with pytest.raises(Exception):
        client.get_json("http://x")
    assert calls["count"] >= 3



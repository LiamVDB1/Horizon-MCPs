from __future__ import annotations

from typing import Any, Dict

import pytest

from helius.client import HeliusClient, _validate_network


def test_validate_network() -> None:
    assert _validate_network("mainnet") == "mainnet"
    assert _validate_network("devnet") == "devnet"
    with pytest.raises(ValueError):
        _validate_network("badnet")


class FakeHttp:
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.calls = []

    def post_json(self, url: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((url, json_body))
        return self.payload

    def get_json(self, url: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.calls.append((url, params))
        return self.payload


def test_rpc_success_result() -> None:
    http = FakeHttp({"jsonrpc": "2.0", "result": {"ok": True}})
    c = HeliusClient(http=http)  # type: ignore[arg-type]
    out = c.rpc("mainnet", "getBalance", ["addr", {}])
    assert out == {"ok": True}


def test_rpc_error_raises() -> None:
    http = FakeHttp({"jsonrpc": "2.0", "error": {"code": -1, "message": "boom"}})
    c = HeliusClient(http=http)  # type: ignore[arg-type]
    with pytest.raises(RuntimeError):
        c.rpc("mainnet", "getBalance", ["addr", {}])


def test_enhanced_and_rpc_urls() -> None:
    http = FakeHttp({})
    c = HeliusClient(http=http)  # type: ignore[arg-type]
    # Just ensure no exceptions in URL building; API key injected from env by conftest
    url = c._enhanced_url("/v0/transactions", "mainnet")
    assert "api-key=" in url and "/v0/transactions" in url
    url2 = c._rpc_url("devnet")
    assert "api-key=" in url2 and "devnet" in url2



from __future__ import annotations

from typing import Any, Dict, List

import pytest

from helius.services import HeliusService


class FakeClient:
    def __init__(self, payload: Any):
        self.payload = payload
        self.calls: List[Dict[str, Any]] = []

    def _enhanced_url(self, path: str, network: str) -> str:  # pragma: no cover
        return f"https://x{path}?api-key=K"

    def rest_post(self, url: str, body: Dict[str, Any]) -> Any:
        self.calls.append({"url": url, "body": body})
        return self.payload

    def rest_get(self, url: str, params: Dict[str, Any]) -> Any:
        self.calls.append({"url": url, "params": params})
        return self.payload

    def rpc(self, network: str, method: str, params: Any) -> Any:
        self.calls.append({"network": network, "method": method, "params": params})
        return self.payload


def test_service_get_transactions_maps_to_models() -> None:
    payload = [
        {
            "signature": "s",
            "slot": 1,
            "status": "success",
            "nativeTransfers": [{"from": "a", "to": "b", "amount": 1}],
        }
    ]
    svc = HeliusService(client=FakeClient(payload))
    out = svc.get_transactions(["s"])
    assert out[0].signature == "s"


def test_service_get_balance_numeric_result() -> None:
    svc = HeliusService(client=FakeClient({"value": 12345}))
    out = svc.get_balance("addr")
    assert out == 12345


def test_service_priority_fee_int_result() -> None:
    svc = HeliusService(client=FakeClient(17))
    out = svc.get_priority_fee_estimate()
    assert isinstance(out, dict) and out["micro_lamports"] == 17



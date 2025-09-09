from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

import MCPs.helius as helius_mcp


class FakeService:
    def get_transactions(self, signatures: List[str], network: str = "mainnet") -> List[Dict[str, Any]]:
        return [{"signature": s} for s in signatures]

    def get_transactions_by_address(
        self,
        address: str,
        network: str = "mainnet",
        tx_type: Optional[str] = None,
        source: Optional[str] = None,
        before: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 50,
        commitment: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return [{"address": address, "limit": limit}]

    def get_balance(self, public_key: str, network: str = "mainnet", commitment: Optional[str] = None) -> int:
        return 42


def test_mcp_tools_call_service(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(helius_mcp, "_service", FakeService())
    out = helius_mcp.get_transactions(["x"])  # type: ignore[arg-type]
    assert out[0]["signature"] == "x"
    bal = helius_mcp.get_balance("addr")
    assert bal == 42



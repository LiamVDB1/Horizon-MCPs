from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    # Prefer global settings from top-level config, fall back to env
    from src.config import settings  # type: ignore
except Exception:
    settings = None  # type: ignore
from src.common.http import HttpClient


HELIUS_ENHANCED_BASES: Dict[str, str] = {
    "mainnet": "https://api.helius.xyz",
    "devnet": "https://api-devnet.helius.xyz",
}

HELIUS_RPC_BASES: Dict[str, str] = {
    "mainnet": "https://mainnet.helius-rpc.com",
    "devnet": "https://devnet.helius-rpc.com",
}


def _require_api_key() -> str:
    api_key: Optional[str] = None
    try:
        api_key = getattr(settings, "HELIUS_API_KEY", None)  # type: ignore[attr-defined]
    except Exception:
        api_key = None
    if not api_key:
        api_key = os.getenv("HELIUS_API_KEY")
    if not api_key:
        raise RuntimeError("HELIUS_API_KEY env var is required.")
    return api_key


def _validate_network(network: str) -> str:
    if network not in ("mainnet", "devnet"):
        raise ValueError("network must be 'mainnet' or 'devnet'")
    return network


class HeliusClient:
    def __init__(self, http: Optional[HttpClient] = None):
        self.http = http or HttpClient()

    def _enhanced_url(self, path: str, network: str) -> str:
        base = HELIUS_ENHANCED_BASES[_validate_network(network)]
        return f"{base}{path}?api-key={_require_api_key()}"

    def _rpc_url(self, network: str) -> str:
        base = HELIUS_RPC_BASES[_validate_network(network)]
        return f"{base}/?api-key={_require_api_key()}"

    # REST helpers
    def rest_get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.http.get_json(url, params=params)

    def rest_post(self, url: str, body: Dict[str, Any]) -> Any:
        return self.http.post_json(url, json_body=body)

    # RPC helper
    def rpc(self, network: str, method: str, params: Any) -> Any:
        payload = {"jsonrpc": "2.0", "id": "helius-mcp", "method": method, "params": params}
        data = self.http.post_json(self._rpc_url(network), payload)
        if isinstance(data, dict) and data.get("error"):
            err = data.get("error") or {}
            raise RuntimeError(f"RPC error {err.get('code')}: {err.get('message')}")
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data



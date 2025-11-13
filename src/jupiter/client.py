from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from src.config import settings  # type: ignore
except Exception:  # pragma: no cover - tests may monkeypatch
    settings = None  # type: ignore

from src.common.http import HttpClient


JUP_BASES: Dict[str, Dict[str, str]] = {
    # family -> tier -> base
    "swap": {"lite": "https://lite-api.jup.ag/swap/v1", "api": "https://api.jup.ag/swap/v1"},
    "ultra": {"lite": "https://lite-api.jup.ag/ultra/v1", "api": "https://api.jup.ag/ultra/v1"},
    "trigger": {"lite": "https://lite-api.jup.ag/trigger/v1", "api": "https://api.jup.ag/trigger/v1"},
    "recurring": {"lite": "https://lite-api.jup.ag/recurring/v1", "api": "https://api.jup.ag/recurring/v1"},
    "tokens": {"lite": "https://lite-api.jup.ag/tokens/v2", "api": "https://api.jup.ag/tokens/v2"},
    "price": {"lite": "https://lite-api.jup.ag/price/v3", "api": "https://api.jup.ag/price/v3"},
    "lend": {"lite": "https://lite-api.jup.ag/lend/v1", "api": "https://api.jup.ag/lend/v1"},
    "send": {"lite": "https://lite-api.jup.ag/send/v1", "api": "https://api.jup.ag/send/v1"},
    "studio": {"lite": "https://lite-api.jup.ag/studio/v1", "api": "https://api.jup.ag/studio/v1"},
}


def _tier() -> str:
    try:
        t = getattr(settings, "JUPITER_TIER", "lite")  # type: ignore[attr-defined]
    except Exception:
        t = "lite"
    if t not in ("lite", "api"):
        return "lite"
    return t


def _api_key() -> Optional[str]:
    try:
        return getattr(settings, "JUPITER_API_KEY", None)  # type: ignore[attr-defined]
    except Exception:
        return None


class JupiterClient:
    def __init__(self, http: Optional[HttpClient] = None):
        self.http = http or HttpClient()

    def _base(self, family: str) -> str:
        t = _tier()
        fam = JUP_BASES.get(family)
        if not fam:
            raise ValueError(f"unknown API family: {family}")
        return fam[t]

    def _headers(self) -> Dict[str, str]:
        hdrs: Dict[str, str] = {}
        if _tier() == "api":
            key = _api_key()
            if key:
                hdrs["x-api-key"] = key
        return hdrs

    # Basic HTTP helpers (with retry/backoff via HttpClient)
    def get(self, family: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self._base(family)}{path}"
        # Inject headers via requests session on-the-fly
        resp = self.http.request_with_retry("get", url, params=params, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def post(self, family: str, path: str, body: Dict[str, Any]) -> Any:
        url = f"{self._base(family)}{path}"
        resp = self.http.request_with_retry("post", url, json=body, headers=self._headers())
        resp.raise_for_status()
        return resp.json()



from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests


class HttpClient:
    def __init__(self, default_timeout_seconds: int = 30):
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self._default_timeout_seconds = default_timeout_seconds

    def request_with_retry(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        backoffs = [0.2, 0.6, 1.2]
        if "timeout" not in kwargs:
            kwargs["timeout"] = self._default_timeout_seconds
        for attempt in range(len(backoffs)):
            resp = self._session.request(method=method.upper(), url=url, **kwargs)
            status = resp.status_code
            if status == 429 or 500 <= status < 600:
                if attempt == len(backoffs) - 1:
                    resp.raise_for_status()
                    return resp
                time.sleep(backoffs[attempt])
                continue
            return resp
        return resp

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = self.request_with_retry("get", url, params=params)
        resp.raise_for_status()
        return resp.json()

    def post_json(self, url: str, json_body: Dict[str, Any]) -> Any:
        resp = self.request_with_retry("post", url, json=json_body)
        resp.raise_for_status()
        return resp.json()



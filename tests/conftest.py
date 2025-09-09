from __future__ import annotations

import os
import sys
import pytest

# Ensure src is importable during collection
_root = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_root, os.pardir))
_src_dir = os.path.join(_project_root, "src")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


@pytest.fixture(autouse=True)
def _fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Only set a fake key if no real key provided
    if "HELIUS_API_KEY" not in os.environ:
        monkeypatch.setenv("HELIUS_API_KEY", "test_api_key")



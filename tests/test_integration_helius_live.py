from __future__ import annotations

import os
import time

import pytest

from helius.services import HeliusService


def _get_api_key() -> str | None:
    try:
        from config import settings as cfg  # type: ignore
        return getattr(cfg, "HELIUS_API_KEY", None)
    except Exception:
        import os as _os
        return _os.getenv("HELIUS_API_KEY")


requires_live = pytest.mark.skipif(
    not _get_api_key(), reason="HELIUS_API_KEY not set; skipping live integration tests"
)


@requires_live
def test_live_get_balance_mainnet() -> None:
    svc = HeliusService()
    # Well-known system account should exist; just verify balance is int and >= 0
    lamports = svc.get_balance("11111111111111111111111111111111", network="mainnet")
    assert isinstance(lamports, int)
    assert lamports >= 0


@requires_live
def test_live_get_signatures_for_address_limit_5() -> None:
    svc = HeliusService()
    # Use a known address (system program) to fetch recent signatures
    signatures = svc.get_signatures_for_address("11111111111111111111111111111111", network="mainnet", limit=5)
    assert isinstance(signatures, list)
    assert len(signatures) <= 5


@requires_live
def test_live_priority_fee_estimate_account_keys() -> None:
    svc = HeliusService()
    # Using system program key in account keys is still valid for estimate endpoint
    res = svc.get_priority_fee_estimate(network="mainnet", account_keys=["11111111111111111111111111111111"])
    assert hasattr(res, "micro_lamports")
    assert isinstance(res.micro_lamports, int)


@requires_live
def test_live_assets_by_owner_zero_page() -> None:
    svc = HeliusService()
    # Random owner with likely zero assets; still should return structure
    res = svc.get_assets_by_owner(owner_address="11111111111111111111111111111111", page=1, limit=1, network="mainnet")
    assert hasattr(res, "items")
    assert isinstance(res.items, list)


@requires_live
def test_live_enhanced_transactions_by_address() -> None:
    svc = HeliusService()
    # Fetch with small limit; may be empty but should return list
    # Use USDC mint (very active address) to increase likelihood of results
    out = svc.get_transactions_by_address("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", network="mainnet", limit=2)
    assert isinstance(out, list)


@requires_live
def test_live_get_transaction_raw_from_recent_signature() -> None:
    svc = HeliusService()
    sigs = svc.get_signatures_for_address("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", network="mainnet", limit=1)
    if not sigs or not sigs[0].signature:
        pytest.skip("No recent signatures to fetch raw transaction")
    tx = svc.get_transaction_raw(sigs[0].signature, network="mainnet")
    # Basic invariants
    assert tx.signature == sigs[0].signature
    assert isinstance(tx.program_ids, list)


@requires_live
def test_live_get_asset_usdc_mint() -> None:
    svc = HeliusService()
    asset = svc.get_asset("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", network="mainnet")
    assert asset.id == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


@requires_live
def test_live_search_assets_fungible_limit_1() -> None:
    svc = HeliusService()
    # Avoid validation requiring owner_address when token_type is specified
    res = svc.search_assets(network="mainnet", limit=1, page=1)
    assert hasattr(res, "items")
    assert isinstance(res.items, list)


@requires_live
def test_live_get_account_info_system_program() -> None:
    svc = HeliusService()
    info = svc.get_account_info("11111111111111111111111111111111", network="mainnet")
    assert info.lamports >= 0
    assert isinstance(info.owner, str) and len(info.owner) > 0


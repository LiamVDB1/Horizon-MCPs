from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import pytest
import requests

from src.jupiter.services import JupiterService
from src.jupiter.client import JupiterClient
from src.jupiter.schemas import (
    SwapQuoteResponse,
    SwapRequest,
    SwapResponse,
    SwapInstructionsResponse,
    UltraHoldingsResponse,
    UltraNativeHoldingsResponse,
    UltraMintInformation,
    RecurringCreateRequest,
    RecurringCloseRequest,
    RecurringGetOrdersResponse,
    SendInviteDataResponse,
    StudioCreateDBCBody,
    StudioCreateDBCResponse,
    StudioClaimFeeBody,
    EarnAmountRequest,
    EarnSharesRequest,
    EarnInstructionResponse,
    EarnTransactionResponse,
    EarnTokensResponse,
    EarnUserPositionsResponse,
    EarnUserEarningsResponse,
    TokenMintInformation,
)
from src.jupiter.schemas.trigger import (
    CreateOrdersRequestBody as TriggerCreateRequest,
    CancelOrderPostRequest as TriggerCancelRequest,
    CancelOrdersRequestBody as TriggerCancelManyRequest,
)
from src.jupiter.schemas.send import (
    CraftSendPostRequest as CraftSendRequest,
    CraftClawbackPostRequest as CraftClawbackRequest,
)


def _get_api_key() -> Optional[str]:
    try:
        from src.config import settings as cfg  # type: ignore
        return getattr(cfg, "JUPITER_API_KEY", None)
    except Exception:
        return os.getenv("JUPITER_API_KEY")


# Do not hard-require API key since lite tier works without it.
requires_live = pytest.mark.skipif(False, reason="Jupiter live tests always run (lite tier available)")


# Test constants - reuse well-known Solana addresses
SYSTEM_PROGRAM = "11111111111111111111111111111111"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL_MINT = "So11111111111111111111111111111111111111112"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
ACTIVE_WALLET = "GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPqn7npE"  # Known active wallet


@requires_live
def test_client_initialization_and_basic_price() -> None:
    client = JupiterClient()
    svc = JupiterService(client)
    assert svc.client is not None

    # Basic connectivity via Price v3
    prices = svc.price_v3([SOL_MINT, USDC_MINT])
    assert isinstance(prices, dict)
    assert SOL_MINT in prices or USDC_MINT in prices


# =============================================================================
# Swap API
# =============================================================================


@requires_live
def test_swap_quote_and_build_and_instructions() -> None:
    svc = JupiterService()

    # Quote a small SOL -> USDC swap
    quote = svc.swap_quote(
        inputMint=SOL_MINT,
        outputMint=USDC_MINT,
        amount=1_000_000,  # 0.001 SOL
        slippageBps=50,
    )
    assert isinstance(quote, SwapQuoteResponse)
    assert quote.inputMint == SOL_MINT
    assert quote.outputMint == USDC_MINT
    assert int(quote.inAmount) == 1_000_000
    assert isinstance(quote.routePlan, list) and len(quote.routePlan) > 0

    # Build unsigned transaction
    req = SwapRequest(userPublicKey=ACTIVE_WALLET, quoteResponse=quote)
    build = svc.swap_build(req)
    assert isinstance(build, dict) and "jupiterResponse" in build
    jr = build["jupiterResponse"]
    assert isinstance(jr, dict)
    assert isinstance(jr.get("swapTransaction"), str)
    assert isinstance(jr.get("lastValidBlockHeight"), int)

    # Request swap instructions
    instr = svc.swap_instructions(req)
    assert isinstance(instr, SwapInstructionsResponse)
    assert isinstance(instr.computeBudgetInstructions, list)
    assert isinstance(instr.setupInstructions, list)
    assert instr.swapInstruction is not None
    assert isinstance(instr.addressLookupTableAddresses, list)


@requires_live
def test_program_id_to_label() -> None:
    svc = JupiterService()
    mapping = svc.program_id_to_label()
    assert isinstance(mapping, dict)
    # Common programs should be labeled
    assert TOKEN_PROGRAM in mapping or len(mapping) > 0


# =============================================================================
# Ultra API
# =============================================================================


@requires_live
def test_ultra_holdings_endpoints() -> None:
    svc = JupiterService()

    holdings = svc.ultra_holdings(ACTIVE_WALLET)
    assert isinstance(holdings, UltraHoldingsResponse)
    assert isinstance(holdings.amount, str)
    assert isinstance(holdings.uiAmount, float)
    assert isinstance(holdings.tokens, dict)

    native = svc.ultra_holdings_native(ACTIVE_WALLET)
    assert isinstance(native, UltraNativeHoldingsResponse)
    assert isinstance(native.amount, str)
    assert isinstance(native.uiAmount, float)


@requires_live
def test_ultra_search_and_shield_and_routers() -> None:
    svc = JupiterService()

    # Search
    tokens = svc.ultra_search("USDC")
    assert isinstance(tokens, list)
    assert any(isinstance(t, UltraMintInformation) for t in tokens)

    # Shield
    warnings = svc.ultra_shield([SOL_MINT, USDC_MINT])
    assert isinstance(warnings, dict)
    # Response shape: { "warnings": { mint: [..], mint: [..] } }
    if "warnings" in warnings and isinstance(warnings["warnings"], dict):
        inner = warnings["warnings"]
        assert isinstance(inner, dict)
        assert all(isinstance(v, list) for v in inner.values())
    else:
        # Some deployments may flatten the shape; accept as long as it is a mapping
        assert isinstance(warnings, dict)

    # Routers
    routers = svc.ultra_routers()
    assert isinstance(routers, list)
    assert len(routers) > 0


@requires_live
def test_ultra_order_quote() -> None:
    svc = JupiterService()
    # No taker provided (service may try to fetch whales but will fall back gracefully)
    result = svc.ultra_order(
        inputMint=USDC_MINT,
        outputMint=SOL_MINT,
        amount="100000",
        simulate=True,
    )
    assert isinstance(result, dict)
    jr = result.get("jupiterResponse")
    sim = result.get("simulation")
    assert isinstance(jr, dict)
    assert isinstance(sim, dict)
    assert jr.get("inputMint") == USDC_MINT
    assert jr.get("outputMint") == SOL_MINT

    assert "requestId" in jr    


@requires_live
def test_ultra_order_with_options() -> None:
    svc = JupiterService()
    # Exercise optional params; accept success or client errors
    try:
        result = svc.ultra_order(
            inputMint=SOL_MINT,
            outputMint=USDC_MINT,
            amount="100000",
            taker=ACTIVE_WALLET,
            referralAccount=ACTIVE_WALLET,
            referralFee=50,
            excludeRouters="metis",
            excludeDexes="Raydium",
            simulate=False,
        )
        assert isinstance(result, dict) and "jupiterResponse" in result
    except requests.HTTPError as e:
        assert e.response is not None and 400 <= e.response.status_code < 600


# =============================================================================
# Trigger API
# =============================================================================


@requires_live
def test_trigger_get_orders() -> None:
    svc = JupiterService()
    resp = svc.trigger_get_orders(user=ACTIVE_WALLET, orderStatus="active")
    # Response is a pydantic model
    assert isinstance(resp.user, str)
    assert resp.orderStatus.value in ("active", "history")
    assert isinstance(resp.orders, list)


@requires_live
def test_trigger_create_and_cancel_endpoints() -> None:
    svc = JupiterService()

    create_body = TriggerCreateRequest(
        inputMint=USDC_MINT,
        outputMint=SOL_MINT,
        maker=ACTIVE_WALLET,
        payer=ACTIVE_WALLET,
        params={"makingAmount": "1000", "takingAmount": "1"},
    )
    # Accept either a proper response or a 4xx error
    try:
        res = svc.trigger_create_order(create_body)
        assert isinstance(res, dict) and "jupiterResponse" in res
    except requests.HTTPError as e:
        assert e.response is not None and 400 <= e.response.status_code < 500

    # Single cancel
    cancel_body = TriggerCancelRequest(maker=ACTIVE_WALLET, order="DummyOrder11111111111111111111111111111111111")
    try:
        res = svc.trigger_cancel_order(cancel_body)
        assert isinstance(res, dict) and "jupiterResponse" in res
    except requests.HTTPError as e:
        assert e.response is not None and 400 <= e.response.status_code < 600

    # Batch cancel
    cancel_many = TriggerCancelManyRequest(maker=ACTIVE_WALLET)
    try:
        res = svc.trigger_cancel_orders(cancel_many)
        assert isinstance(res, dict) and "jupiterResponse" in res
    except requests.HTTPError as e:
        assert e.response is not None and 400 <= e.response.status_code < 500


# =============================================================================
# Recurring API
# =============================================================================


@requires_live
def test_recurring_get_orders() -> None:
    svc = JupiterService()
    try:
        data = svc.recurring_get_orders(
            recurringType="all", orderStatus="active", user=ACTIVE_WALLET, includeFailedTx=True
        )
        assert isinstance(data, dict)
        assert data.get("orderStatus") in ("active", "history")
        assert "page" in data and "totalPages" in data
    except requests.HTTPError as e:
        # Accept 400s when the wallet has no recurring orders or invalid params expectations
        assert e.response is not None and 400 <= e.response.status_code < 500


@requires_live
def test_recurring_create_and_cancel_endpoints() -> None:
    svc = JupiterService()
    create = RecurringCreateRequest(
        user=ACTIVE_WALLET,
        inputMint=SOL_MINT,
        outputMint=USDC_MINT,
        params={
            "time": {
                "inAmount": 1000,
                "numberOfOrders": 2,
                "interval": 60,
            }
        },
    )
    try:
        res = svc.recurring_create_order(create)
        assert isinstance(res, dict) and "jupiterResponse" in res
    except requests.HTTPError as e:
        assert e.response is not None and 400 <= e.response.status_code < 500

    close = RecurringCloseRequest(user=ACTIVE_WALLET, order="DummyRecurring111111111111111111111111111111111", recurringType="time")
    try:
        res = svc.recurring_cancel_order(close)
        assert isinstance(res, dict) and "jupiterResponse" in res
    except requests.HTTPError as e:
        assert e.response is not None and 400 <= e.response.status_code < 600


# =============================================================================
# Token and Price APIs
# =============================================================================


@requires_live
def test_token_endpoints_and_price_v3() -> None:
    svc = JupiterService()

    search = svc.token_search("USDC")
    assert isinstance(search, list)
    assert any(isinstance(it, TokenMintInformation) for it in search)

    verified = svc.token_tag("verified")
    assert isinstance(verified, list)

    top = svc.token_category("toptraded", "24h", limit=10)
    assert isinstance(top, list)
    assert 0 < len(top) <= 10

    recent = svc.token_recent()
    assert isinstance(recent, list)

    prices = svc.price_v3([SOL_MINT, USDC_MINT])
    assert isinstance(prices, dict)
    for item in prices.values():
        assert hasattr(item, "decimals") and hasattr(item, "usdPrice")


# =============================================================================
# Lend / Earn API
# =============================================================================


@requires_live
def test_earn_tokens_and_positions_and_optionally_earnings() -> None:
    svc = JupiterService()

    tokens = svc.earn_tokens()
    assert isinstance(tokens, list)
    if tokens:
        t0 = tokens[0]
        assert hasattr(t0, "address") and isinstance(t0.address, str)

    positions = svc.earn_positions([ACTIVE_WALLET])
    assert isinstance(positions, list)

    # If we have any positions, try fetching earnings for up to 2
    if positions:
        pos_ids = [p.token.address for p in positions[:2] if getattr(p, "token", None) and getattr(p.token, "address", None)]
        if pos_ids:
            try:
                earnings = svc.earn_earnings(user=ACTIVE_WALLET, positions=pos_ids)
                assert hasattr(earnings, "address") and earnings.ownerAddress == ACTIVE_WALLET
            except requests.HTTPError as e:
                # Accept upstream errors (e.g., 4xx/5xx) as long as request plumbing works
                assert e.response is not None and 400 <= e.response.status_code < 600


@requires_live
def test_earn_transaction_endpoints() -> None:
    svc = JupiterService()
    # Try transaction endpoints; expect either tx data or 4xx
    asset = USDC_MINT
    signer = ACTIVE_WALLET
    amt = EarnAmountRequest(asset=asset, signer=signer, amount="1000")
    shr = EarnSharesRequest(asset=asset, signer=signer, shares="1000")

    for fn in (svc.earn_deposit, svc.earn_withdraw):
        try:
            res = fn(amt)
            assert isinstance(res, dict) and "jupiterResponse" in res
        except requests.HTTPError as e:
            assert e.response is not None and 400 <= e.response.status_code < 500

    for fn in (svc.earn_mint, svc.earn_redeem):
        try:
            res = fn(shr)
            assert isinstance(res, dict) and "jupiterResponse" in res
        except requests.HTTPError as e:
            assert e.response is not None and 400 <= e.response.status_code < 500


@requires_live
def test_earn_instruction_endpoints() -> None:
    svc = JupiterService()

    # Use an available earn token if possible; fallback to USDC
    earn_tokens = svc.earn_tokens()
    asset = earn_tokens[0].address if earn_tokens else USDC_MINT
    signer = ACTIVE_WALLET

    # These endpoints should return instruction structures or raise 4xx; both are acceptable
    body_amt = EarnAmountRequest(asset=asset, signer=signer, amount="1000")
    body_shares = EarnSharesRequest(asset=asset, signer=signer, shares="1000")

    for fn in (
        svc.earn_deposit_instructions,
        svc.earn_withdraw_instructions,
    ):
        try:
            instr = fn(body_amt)
            assert isinstance(instr, EarnInstructionResponse)
            assert isinstance(instr.programId, str)
            assert isinstance(instr.accounts, list)
            assert isinstance(instr.data, str)
        except requests.HTTPError as e:
            # Acceptable for invalid asset/amount combinations
            assert e.response is not None and 400 <= e.response.status_code < 500

    for fn in (
        svc.earn_mint_instructions,
        svc.earn_redeem_instructions,
    ):
        try:
            instr = fn(body_shares)
            assert isinstance(instr, EarnInstructionResponse)
            assert isinstance(instr.programId, str)
            assert isinstance(instr.accounts, list)
            assert isinstance(instr.data, str)
        except requests.HTTPError as e:
            assert e.response is not None and 400 <= e.response.status_code < 500


# =============================================================================
# Send API
# =============================================================================


@requires_live
def test_send_pending_and_history() -> None:
    svc = JupiterService()
    pending = svc.send_pending_invites(ACTIVE_WALLET)
    history = svc.send_invite_history(ACTIVE_WALLET)
    assert isinstance(pending, SendInviteDataResponse)
    assert isinstance(history, SendInviteDataResponse)


@requires_live
def test_send_craft_and_clawback_endpoints() -> None:
    svc = JupiterService()
    craft = CraftSendRequest(inviteSigner=SYSTEM_PROGRAM, sender=ACTIVE_WALLET, amount="1000", mint=USDC_MINT)
    try:
        res = svc.send_craft(craft)
        assert isinstance(res, dict) and "jupiterResponse" in res
    except requests.HTTPError as e:
        assert e.response is not None and 400 <= e.response.status_code < 500

    claw = CraftClawbackRequest(invitePDA=SYSTEM_PROGRAM, sender=ACTIVE_WALLET)
    try:
        res = svc.send_craft_clawback(claw)
        assert isinstance(res, dict) and "jupiterResponse" in res
    except requests.HTTPError as e:
        assert e.response is not None and 400 <= e.response.status_code < 600


# =============================================================================
# Performance / Rate Limiting Basic Check
# =============================================================================


@requires_live
def test_sequential_requests_performance() -> None:
    svc = JupiterService()
    start = time.time()

    _ = svc.price_v3([SOL_MINT, USDC_MINT])
    _ = svc.token_recent()
    _ = svc.ultra_routers()

    elapsed = time.time() - start
    assert elapsed < 30



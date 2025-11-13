"""
Jupiter MCP server: read-only + unsigned transaction/instruction builders (no execute).
Simulate option integrates with Helius simulateTransaction.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from fastmcp import FastMCP

from src.jupiter.services import JupiterService
from src.jupiter.schemas.swap import SwapRequest
from src.jupiter.schemas.trigger import CreateOrdersRequestBody as TriggerCreateRequest, CancelOrderPostRequest as TriggerCancelRequest, CancelOrdersRequestBody as TriggerCancelManyRequest
from src.jupiter.schemas.recurring import CreateRecurring as RecurringCreateRequest, CloseRecurring as RecurringCloseRequest
from src.jupiter.schemas.lend_earn import EarnAmountRequestBody as EarnAmountRequest, EarnSharesRequestBody as EarnSharesRequest
from src.jupiter.schemas.send import CraftSendPostRequest as CraftSendRequest, CraftClawbackPostRequest as CraftClawbackRequest
from src.jupiter.schemas.studio import CreateDBCTransactionRequestBody, CreateClaimFeeDBCTransactionRequestBody


mcp = FastMCP(
    "jupiter-mcp",
    "Jupiter API MCP: quotes, builders, read APIs; never execute. Optional simulate via Helius.",
)

_svc = JupiterService()


def _dump(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, list):
        return [ _dump(x) for x in obj ]
    return obj


# --- swap ---

def swap_quote(
    inputMint: str,
    outputMint: str,
    amount: int,
    slippageBps: Optional[int] = None,
    swapMode: Optional[str] = None,
    dexes: Optional[List[str]] = None,
    excludeDexes: Optional[List[str]] = None,
    restrictIntermediateTokens: Optional[bool] = None,
    onlyDirectRoutes: Optional[bool] = None,
    asLegacyTransaction: Optional[bool] = None,
    platformFeeBps: Optional[int] = None,
    maxAccounts: Optional[int] = None,
    dynamicSlippage: Optional[bool] = None,
) -> Dict[str, Any]:
    q = _svc.swap_quote(
        inputMint,
        outputMint,
        amount,
        slippageBps,
        swapMode,
        dexes,
        excludeDexes,
        restrictIntermediateTokens,
        onlyDirectRoutes,
        asLegacyTransaction,
        platformFeeBps,
        maxAccounts,
        dynamicSlippage,
    )
    return q.model_dump()


def swap_build(request: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    body = SwapRequest.model_validate(request)
    return _svc.swap_build(body, simulate=simulate, simulate_opts=simulate_opts, network=network)


def swap_instructions(request: Dict[str, Any]) -> Dict[str, Any]:
    body = SwapRequest.model_validate(request)
    return _dump(_svc.swap_instructions(body))


def swap_programIdToLabel() -> Dict[str, str]:
    return _svc.program_id_to_label()


# --- ultra ---

def ultra_holdings(address: str) -> Dict[str, Any]:
    return _svc.ultra_holdings(address).model_dump()


def ultra_holdingsNative(address: str) -> Dict[str, Any]:
    return _svc.ultra_holdings_native(address).model_dump()


def ultra_search(query: str) -> List[Dict[str, Any]]:
    return [it.model_dump() for it in _svc.ultra_search(query)]


def ultra_shield(mints: List[str]) -> Dict[str, Any]:
    return _svc.ultra_shield(mints)


def ultra_order(
    inputMint: str,
    outputMint: str,
    amount: str,
    taker: Optional[str] = None,
    referralAccount: Optional[str] = None,
    referralFee: Optional[int] = None,
    excludeRouters: Optional[str] = None,
    excludeDexes: Optional[str] = None,
    simulate: bool = False,
    simulate_opts: Optional[Dict[str, Any]] = None,
    network: str = "mainnet",
) -> Dict[str, Any]:
    return _svc.ultra_order(
        inputMint,
        outputMint,
        amount,
        taker,
        referralAccount,
        referralFee,
        excludeRouters,
        excludeDexes,
        simulate,
        simulate_opts,
        network,
    )


def ultra_routers() -> List[Dict[str, Any]]:
    return _svc.ultra_routers()


# --- trigger ---

def trigger_createOrder(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = TriggerCreateRequest.model_validate(body)
    return _svc.trigger_create_order(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def trigger_cancelOrder(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = TriggerCancelRequest.model_validate(body)
    return _svc.trigger_cancel_order(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def trigger_cancelOrders(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = TriggerCancelManyRequest.model_validate(body)
    return _svc.trigger_cancel_orders(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def trigger_getOrders(
    user: str,
    orderStatus: str,
    page: Optional[str] = None,
    includeFailedTx: Optional[str] = None,
    inputMint: Optional[str] = None,
    outputMint: Optional[str] = None,
) -> Dict[str, Any]:
    return _svc.trigger_get_orders(user, orderStatus, page, includeFailedTx, inputMint, outputMint)


# --- recurring ---

def recurring_createOrder(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = RecurringCreateRequest.model_validate(body)
    return _svc.recurring_create_order(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def recurring_cancelOrder(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = RecurringCloseRequest.model_validate(body)
    return _svc.recurring_cancel_order(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def recurring_getOrders(
    recurringType: str,
    orderStatus: str,
    user: str,
    includeFailedTx: bool,
    page: Optional[int] = None,
    mint: Optional[str] = None,
) -> Dict[str, Any]:
    return _svc.recurring_get_orders(recurringType, orderStatus, user, includeFailedTx, page, mint)


# --- token v2 ---

def token_search(query: str) -> List[Dict[str, Any]]:
    return [it.model_dump() for it in _svc.token_search(query)]


def token_tag(query: str) -> List[Dict[str, Any]]:
    return [it.model_dump() for it in _svc.token_tag(query)]


def token_category(category: str, interval: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    return [it.model_dump() for it in _svc.token_category(category, interval, limit)]


def token_recent() -> List[Dict[str, Any]]:
    return [it.model_dump() for it in _svc.token_recent()]


# --- price v3 ---

def price_v3(ids: List[str]) -> Dict[str, Dict[str, Any]]:
    out = _svc.price_v3(ids)
    return {k: v.model_dump() for k, v in out.items()}


# --- earn ---

def earn_deposit(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = EarnAmountRequest.model_validate(body)
    return _svc.earn_deposit(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def earn_withdraw(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = EarnAmountRequest.model_validate(body)
    return _svc.earn_withdraw(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def earn_mint(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = EarnSharesRequest.model_validate(body)
    return _svc.earn_mint(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def earn_redeem(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = EarnSharesRequest.model_validate(body)
    return _svc.earn_redeem(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def earn_depositInstructions(body: Dict[str, Any]) -> Dict[str, Any]:
    req = EarnAmountRequest.model_validate(body)
    return _svc.earn_deposit_instructions(req).model_dump()


def earn_withdrawInstructions(body: Dict[str, Any]) -> Dict[str, Any]:
    req = EarnAmountRequest.model_validate(body)
    return _svc.earn_withdraw_instructions(req).model_dump()


def earn_mintInstructions(body: Dict[str, Any]) -> Dict[str, Any]:
    req = EarnSharesRequest.model_validate(body)
    return _svc.earn_mint_instructions(req).model_dump()


def earn_redeemInstructions(body: Dict[str, Any]) -> Dict[str, Any]:
    req = EarnSharesRequest.model_validate(body)
    return _svc.earn_redeem_instructions(req).model_dump()


def earn_tokens() -> List[Dict[str, Any]]:
    return [it.model_dump() for it in _svc.earn_tokens()]


def earn_positions(users: List[str]) -> List[Dict[str, Any]]:
    return [it.model_dump() for it in _svc.earn_positions(users)]


def earn_earnings(user: str, positions: List[str]) -> Dict[str, Any]:
    return _svc.earn_earnings(user, positions).model_dump()


# --- send ---

def send_craft(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = CraftSendRequest.model_validate(body)
    return _svc.send_craft(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def send_craftClawback(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = CraftClawbackRequest.model_validate(body)
    return _svc.send_craft_clawback(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def send_pendingInvites(address: str, page: Optional[int] = None) -> Dict[str, Any]:
    return _svc.send_pending_invites(address, page).model_dump()


def send_inviteHistory(address: str, page: Optional[int] = None) -> Dict[str, Any]:
    return _svc.send_invite_history(address, page).model_dump()


# --- studio ---

def studio_dbc_createPoolTx(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = CreateDBCTransactionRequestBody.model_validate(body)
    return _svc.studio_dbc_create_pool_tx(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def studio_dbc_feeCreateTx(body: Dict[str, Any], simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
    req = CreateClaimFeeDBCTransactionRequestBody.model_validate(body)
    return _svc.studio_dbc_fee_create_tx(req, simulate=simulate, simulate_opts=simulate_opts, network=network)


def studio_dbc_poolAddressesByMint(mint: str) -> Dict[str, Any]:
    return _svc.studio_dbc_pool_addresses_by_mint(mint)


def studio_dbc_fee(poolAddress: str) -> Dict[str, Any]:
    return _svc.studio_dbc_fee(poolAddress)


def register_mcp_tools() -> None:
    # swap
    mcp.tool(name="swap.quote")(swap_quote)
    mcp.tool(name="swap.build")(swap_build)
    mcp.tool(name="swap.instructions")(swap_instructions)
    mcp.tool(name="swap.programIdToLabel")(swap_programIdToLabel)

    # ultra
    mcp.tool(name="ultra.holdings")(ultra_holdings)
    mcp.tool(name="ultra.holdingsNative")(ultra_holdingsNative)
    mcp.tool(name="ultra.search")(ultra_search)
    mcp.tool(name="ultra.shield")(ultra_shield)
    mcp.tool(name="ultra.order")(ultra_order)
    mcp.tool(name="ultra.routers")(ultra_routers)

    # trigger
    mcp.tool(name="trigger.createOrder")(trigger_createOrder)
    mcp.tool(name="trigger.cancelOrder")(trigger_cancelOrder)
    mcp.tool(name="trigger.cancelOrders")(trigger_cancelOrders)
    mcp.tool(name="trigger.getOrders")(trigger_getOrders)

    # recurring
    mcp.tool(name="recurring.createOrder")(recurring_createOrder)
    mcp.tool(name="recurring.cancelOrder")(recurring_cancelOrder)
    mcp.tool(name="recurring.getOrders")(recurring_getOrders)

    # token
    mcp.tool(name="token.search")(token_search)
    mcp.tool(name="token.tag")(token_tag)
    mcp.tool(name="token.category")(token_category)
    mcp.tool(name="token.recent")(token_recent)

    # price
    mcp.tool(name="price.v3")(price_v3)

    # earn
    mcp.tool(name="earn.deposit")(earn_deposit)
    mcp.tool(name="earn.withdraw")(earn_withdraw)
    mcp.tool(name="earn.mint")(earn_mint)
    mcp.tool(name="earn.redeem")(earn_redeem)
    mcp.tool(name="earn.depositInstructions")(earn_depositInstructions)
    mcp.tool(name="earn.withdrawInstructions")(earn_withdrawInstructions)
    mcp.tool(name="earn.mintInstructions")(earn_mintInstructions)
    mcp.tool(name="earn.redeemInstructions")(earn_redeemInstructions)
    mcp.tool(name="earn.tokens")(earn_tokens)
    mcp.tool(name="earn.positions")(earn_positions)
    mcp.tool(name="earn.earnings")(earn_earnings)

    # send
    mcp.tool(name="send.craft")(send_craft)
    mcp.tool(name="send.craftClawback")(send_craftClawback)
    mcp.tool(name="send.pendingInvites")(send_pendingInvites)
    mcp.tool(name="send.inviteHistory")(send_inviteHistory)

    # studio
    mcp.tool(name="studio.dbc.createPoolTx")(studio_dbc_createPoolTx)
    mcp.tool(name="studio.dbc.feeCreateTx")(studio_dbc_feeCreateTx)
    mcp.tool(name="studio.dbc.poolAddressesByMint")(studio_dbc_poolAddressesByMint)
    mcp.tool(name="studio.dbc.fee")(studio_dbc_fee)


if __name__ == "__main__":
    register_mcp_tools()
    mcp.run(transport="streamable-http", host="127.0.0.1", port=9121, path="/mcp")



from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .client import JupiterClient
from . import transforms as tf
from . import schemas as sc
from src.helius.services import HeliusService


class JupiterService:
    def __init__(self, client: Optional[JupiterClient] = None, helius: Optional[HeliusService] = None):
        self.client = client or JupiterClient()
        self.helius = helius or HeliusService()

    # --- Swap API ---
    def swap_quote(
        self,
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
    ) -> sc.QuoteResponse:
        params: Dict[str, Any] = {
            "inputMint": inputMint,
            "outputMint": outputMint,
            "amount": amount,
            "slippageBps": slippageBps,
            "swapMode": swapMode,
            "dexes": ",".join(dexes) if isinstance(dexes, list) else None,
            "excludeDexes": ",".join(excludeDexes) if isinstance(excludeDexes, list) else None,
            "restrictIntermediateTokens": restrictIntermediateTokens,
            "onlyDirectRoutes": onlyDirectRoutes,
            "asLegacyTransaction": asLegacyTransaction,
            "platformFeeBps": platformFeeBps,
            "maxAccounts": maxAccounts,
            "dynamicSlippage": dynamicSlippage,
        }
        raw = self.client.get("swap", "/quote", params=tf.shape_query(params))
        return sc.QuoteResponse.model_validate(raw)

    def _sim_args(self, simulate_opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        opts = simulate_opts or {}
        return {
            "sig_verify": bool(opts.get("sigVerify")) if isinstance(opts.get("sigVerify"), bool) else False,
            "commitment": opts.get("commitment"),
        }

    def swap_build(
        self,
        request: sc.SwapRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("swap", "/swap", request.model_dump())
        out = {"jupiterResponse": sc.SwapResponse.model_validate(raw).model_dump()}
        if simulate:
            tx_b64 = out["jupiterResponse"]["swapTransaction"]
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx_b64, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def swap_instructions(self, request: sc.SwapRequest) -> sc.SwapInstructionsResponse:
        raw = self.client.post("swap", "/swap-instructions", request.model_dump())
        return sc.SwapInstructionsResponse.model_validate(raw)

    def program_id_to_label(self) -> Dict[str, str]:
        return self.client.get("swap", "/program-id-to-label")

    # --- Ultra API ---
    def ultra_holdings(self, address: str) -> sc.HoldingsResponse:
        raw = self.client.get("ultra", f"/holdings/{address}")
        return sc.HoldingsResponse.model_validate(raw)

    def ultra_holdings_native(self, address: str) -> sc.NativeHoldingsResponse:
        raw = self.client.get("ultra", f"/holdings/{address}/native")
        return sc.NativeHoldingsResponse.model_validate(raw)

    def ultra_search(self, query: str) -> List[sc.MintInformation]:
        raw = self.client.get("ultra", "/search", params={"query": query})
        return [sc.MintInformation.model_validate(it) for it in raw]

    def ultra_shield(self, mints: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        raw = self.client.get("ultra", "/shield", params={"mints": tf.comma_join(mints)})
        return raw

    def ultra_order(
        self,
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
        if not taker:
            try:
                whales = self.helius.get_token_whale_addresses(inputMint, network=network)
                taker = tf.choose_taker_from_whales(whales) or taker
            except Exception:
                pass
        params: Dict[str, Any] = {
            "inputMint": inputMint,
            "outputMint": outputMint,
            "amount": amount,
            "taker": taker,
            "referralAccount": referralAccount,
            "referralFee": referralFee,
            "excludeRouters": excludeRouters,
            "excludeDexes": excludeDexes,
        }
        raw = self.client.get("ultra", "/order", params=tf.shape_query(params))
        order = sc.UltraOrderResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": order.model_dump()}
        if simulate and order.transaction:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(order.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def ultra_routers(self) -> List[Dict[str, Any]]:
        raw = self.client.get("ultra", "/order/routers")
        return raw

    # --- Trigger API ---
    def trigger_create_order(
        self,
        body: sc.TriggerCreateRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("trigger", "/createOrder", body.model_dump())
        resp = sc.TriggerTransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate:
            tx = resp.transaction
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def trigger_cancel_order(
        self,
        body: sc.TriggerCancelRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("trigger", "/cancelOrder", body.model_dump())
        resp = sc.TriggerTransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def trigger_cancel_orders(
        self,
        body: sc.TriggerCancelManyRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("trigger", "/cancelOrders", body.model_dump())
        # Response here returns { requestId, transactions: [base64...] }
        out: Dict[str, Any] = {"jupiterResponse": raw}
        if simulate:
            txs: List[str] = raw.get("transactions") if isinstance(raw, dict) else []
            if isinstance(txs, list):
                sargs = self._sim_args(simulate_opts)
                sims = [self.helius.simulate_transaction(tx, network=network, **sargs) for tx in txs]
                out["simulation"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in sims]
        return out

    def trigger_get_orders(
        self,
        user: str,
        orderStatus: str,
        page: Optional[str] = None,
        includeFailedTx: Optional[str] = None,
        inputMint: Optional[str] = None,
        outputMint: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = tf.shape_query(
            {
                "user": user,
                "orderStatus": orderStatus,
                "page": page,
                "includeFailedTx": includeFailedTx,
                "inputMint": inputMint,
                "outputMint": outputMint,
            }
        )
        return self.client.get("trigger", "/getTriggerOrders", params=params)

    # --- Recurring API (time) ---
    def recurring_create_order(
        self,
        body: sc.RecurringCreateRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("recurring", "/createOrder", body.model_dump())
        resp = sc.RecurringResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def recurring_cancel_order(
        self,
        body: sc.RecurringCloseRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("recurring", "/cancelOrder", body.model_dump())
        resp = sc.RecurringResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def recurring_get_orders(
        self,
        recurringType: str,
        orderStatus: str,
        user: str,
        includeFailedTx: bool,
        page: Optional[int] = None,
        mint: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = tf.shape_query(
            {
                "recurringType": recurringType,
                "orderStatus": orderStatus,
                "user": user,
                "includeFailedTx": includeFailedTx,
                "page": page,
                "mint": mint,
            }
        )
        return self.client.get("recurring", "/getRecurringOrders", params=params)

    # --- Token v2 ---
    def token_search(self, query: str) -> List[sc.MintInformation]:
        raw = self.client.get("tokens", "/search", params={"query": query})
        return [sc.MintInformation.model_validate(it) for it in raw]

    def token_tag(self, query: str) -> List[sc.MintInformation]:
        raw = self.client.get("tokens", "/tag", params={"query": query})
        return [sc.MintInformation.model_validate(it) for it in raw]

    def token_category(self, category: str, interval: str, limit: Optional[int] = None) -> List[sc.MintInformation]:
        params = tf.shape_query({"limit": limit})
        raw = self.client.get("tokens", f"/{category}/{interval}", params=params)
        return [sc.MintInformation.model_validate(it) for it in raw]

    def token_recent(self) -> List[sc.MintInformation]:
        raw = self.client.get("tokens", "/recent")
        return [sc.MintInformation.model_validate(it) for it in raw]

    # --- Price v3 ---
    def price_v3(self, ids: List[str]) -> Dict[str, sc.PriceItem]:
        raw = self.client.get("price", "", params={"ids": tf.comma_join(ids)})
        return {k: sc.PriceItem.model_validate(v) for k, v in raw.items()}

    # --- Lend/Earn ---
    def earn_deposit(self, body: sc.EarnAmountRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("lend", "/earn/deposit", body.model_dump())
        tx = sc.TransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": tx.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def earn_withdraw(self, body: sc.EarnAmountRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("lend", "/earn/withdraw", body.model_dump())
        tx = sc.TransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": tx.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def earn_mint(self, body: sc.EarnAmountRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("lend", "/earn/mint", body.model_dump())
        tx = sc.TransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": tx.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def earn_redeem(self, body: sc.EarnAmountRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("lend", "/earn/redeem", body.model_dump())
        tx = sc.TransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": tx.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def earn_deposit_instructions(self, body: sc.EarnAmountRequest) -> sc.InstructionResponse:
        raw = self.client.post("lend", "/earn/deposit-instructions", body.model_dump())
        return sc.InstructionResponse.model_validate(raw)

    def earn_withdraw_instructions(self, body: sc.EarnAmountRequest) -> sc.InstructionResponse:
        raw = self.client.post("lend", "/earn/withdraw-instructions", body.model_dump())
        return sc.InstructionResponse.model_validate(raw)

    def earn_mint_instructions(self, body: sc.EarnSharesRequest) -> sc.InstructionResponse:
        raw = self.client.post("lend", "/earn/mint-instructions", body.model_dump())
        return sc.InstructionResponse.model_validate(raw)

    def earn_redeem_instructions(self, body: sc.EarnSharesRequest) -> sc.InstructionResponse:
        raw = self.client.post("lend", "/earn/redeem-instructions", body.model_dump())
        return sc.InstructionResponse.model_validate(raw)

    def earn_tokens(self) -> List[sc.TokenInfo]:
        raw = self.client.get("lend", "/earn/tokens")
        return [sc.TokenInfo.model_validate(it) for it in raw]

    def earn_positions(self, users: List[str]) -> List[sc.UserPosition]:
        raw = self.client.get("lend", "/earn/positions", params={"users": tf.comma_join(users)})
        return [sc.UserPosition.model_validate(it) for it in raw]

    def earn_earnings(self, user: str, positions: List[str]) -> Dict[str, Any]:
        raw = self.client.get("lend", "/earn/earnings", params={"user": user, "positions": tf.comma_join(positions)})
        return raw

    # --- Send API ---
    def send_craft(self, body: sc.CraftSendRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("send", "/craft-send", body.model_dump())
        resp = sc.CraftSendResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.tx, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def send_craft_clawback(self, body: sc.CraftClawbackRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("send", "/craft-clawback", body.model_dump())
        resp = sc.CraftClawbackResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.tx, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def send_pending_invites(self, address: str, page: Optional[int] = None) -> Dict[str, Any]:
        params = tf.shape_query({"address": address, "page": page})
        return self.client.get("send", "/pending-invites", params=params)

    def send_invite_history(self, address: str, page: Optional[int] = None) -> Dict[str, Any]:
        params = tf.shape_query({"address": address, "page": page})
        return self.client.get("send", "/invite-history", params=params)

    # --- Studio (DBC) ---
    def studio_dbc_create_pool_tx(
        self,
        body: sc.CreateDBCTransactionRequestBody,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("studio", "/dbc-pool/create-tx", body.model_dump())
        resp = sc.CreateDBCTransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def studio_dbc_fee_create_tx(
        self,
        body: sc.CreateClaimFeeDBCTransactionRequestBody,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("studio", "/dbc/fee/create-tx", body.model_dump())
        resp = raw  # { transaction: string }
        out: Dict[str, Any] = {"jupiterResponse": resp}
        if simulate and isinstance(resp, dict) and isinstance(resp.get("transaction"), str):
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp["transaction"], network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def studio_dbc_pool_addresses_by_mint(self, mint: str) -> Dict[str, Any]:
        return self.client.get("studio", f"/dbc-pool/addresses/{mint}")

    def studio_dbc_fee(self, poolAddress: str) -> Dict[str, Any]:
        return self.client.post("studio", "/dbc/fee", {"poolAddress": poolAddress})



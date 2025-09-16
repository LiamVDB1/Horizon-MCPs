from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .client import JupiterClient
from . import transforms as tf
from .schemas.swap import QuoteResponse, SwapRequest, SwapResponse, SwapInstructionsResponse
from .schemas.ultra import HoldingsResponse, NativeHoldingsResponse, MintInformation as UltraMintInformation, OrderGetResponse as UltraOrderResponse
from .schemas.trigger import CreateOrdersRequestBody as TriggerCreateRequest, CreateOrderPostResponse as TriggerTransactionResponse, CancelOrderPostRequest as TriggerCancelRequest, CancelOrdersRequestBody as TriggerCancelManyRequest, GetTriggerOrdersGetResponse
from .schemas.recurring import CreateRecurring as RecurringCreateRequest, RecurringResponse, CloseRecurring as RecurringCloseRequest
from .schemas.token_v2 import MintInformation as TokenMintInformation
from .schemas.price_v3 import FieldDatamodelCodeGeneratorRootSpecialGetResponse1 as PriceItem
from .schemas.lend_earn import EarnAmountRequestBody as EarnAmountRequest, EarnSharesRequestBody as EarnSharesRequest, TransactionResponse, InstructionResponse, TokenInfo, UserPosition, UserEarningsResponse
from .schemas.send import CraftSendPostRequest as CraftSendRequest, CraftSendPostResponse as CraftSendResponse, CraftClawbackPostRequest as CraftClawbackRequest, CraftClawbackPostResponse as CraftClawbackResponse, InviteDataResponse
from .schemas.studio import CreateDBCTransactionRequestBody, CreateDBCTransactionResponse, CreateClaimFeeDBCTransactionRequestBody
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
    ) -> QuoteResponse:
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
        return QuoteResponse.model_validate(raw)

    def _sim_args(self, simulate_opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        opts = simulate_opts or {}
        return {
            "sig_verify": bool(opts.get("sigVerify")) if isinstance(opts.get("sigVerify"), bool) else False,
            "commitment": opts.get("commitment"),
        }

    def swap_build(
        self,
        request: SwapRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        # Ensure enums and nested models are JSON-serializable
        raw = self.client.post("swap", "/swap", request.model_dump(mode="json"))
        resp = SwapResponse.model_validate(raw)
        out = {"jupiterResponse": resp.model_dump()}
        if simulate and resp.swapTransaction:
            tx_b64 = resp.swapTransaction
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx_b64, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def swap_instructions(self, request: SwapRequest) -> SwapInstructionsResponse:
        raw = self.client.post("swap", "/swap-instructions", request.model_dump(mode="json"))
        return SwapInstructionsResponse.model_validate(raw)

    def program_id_to_label(self) -> Dict[str, str]:
        return self.client.get("swap", "/program-id-to-label")

    # --- Ultra API ---
    def ultra_holdings(self, address: str) -> HoldingsResponse:
        raw = self.client.get("ultra", f"/holdings/{address}")
        return HoldingsResponse.model_validate(raw)

    def ultra_holdings_native(self, address: str) -> NativeHoldingsResponse:
        raw = self.client.get("ultra", f"/holdings/{address}/native")
        return NativeHoldingsResponse.model_validate(raw)

    def ultra_search(self, query: str) -> List[UltraMintInformation]:
        raw = self.client.get("ultra", "/search", params={"query": query})
        return [UltraMintInformation.model_validate(it) for it in raw]

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
        if not taker and simulate:
            try:
                taker = self.helius.get_token_whale_addresses(inputMint, network=network, min_amount_ui=float(amount))
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
        try:
            order = UltraOrderResponse.model_validate(raw)
        except Exception as e:
            print(raw)
            print(e)
            raise e
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
        body: TriggerCreateRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("trigger", "/createOrder", body.model_dump(mode="json"))
        resp = TriggerTransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate and resp.transaction:
            tx = resp.transaction
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def trigger_cancel_order(
        self,
        body: TriggerCancelRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("trigger", "/cancelOrder", body.model_dump(mode="json"))
        resp = TriggerTransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate and resp.transactions:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def trigger_cancel_orders(
        self,
        body: TriggerCancelManyRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("trigger", "/cancelOrders", body.model_dump())
        # Response here returns { requestId, transactions: [base64...] }
        out: Dict[str, Any] = {"jupiterResponse": raw}
        #TODO Model validate the response
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
    ) -> GetTriggerOrdersGetResponse:
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
        raw = self.client.get("trigger", "/getTriggerOrders", params=params)
        return GetTriggerOrdersGetResponse.model_validate(raw)        

    # --- Recurring API (time) ---
    def recurring_create_order(
        self,
        body: RecurringCreateRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("recurring", "/createOrder", body.model_dump())
        resp = RecurringResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate and resp.transaction:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def recurring_cancel_order(
        self,
        body: RecurringCloseRequest,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("recurring", "/cancelOrder", body.model_dump(mode="json"))
        resp = RecurringResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate and resp.transaction:
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
        # API expects 'true'/'false' strings for includeFailedTx
        params = tf.shape_query(
            {
                "recurringType": recurringType,
                "orderStatus": orderStatus,
                "user": user,
                "includeFailedTx": str(includeFailedTx).lower(),
                "page": page,
                "mint": mint,
            }
        )
        return self.client.get("recurring", "/getRecurringOrders", params=params)

    # --- Token v2 ---
    def token_search(self, query: str) -> List[TokenMintInformation]:
        raw = self.client.get("tokens", "/search", params={"query": query})
        return [TokenMintInformation.model_validate(it) for it in raw]

    def token_tag(self, query: str) -> List[TokenMintInformation]:
        raw = self.client.get("tokens", "/tag", params={"query": query})
        return [TokenMintInformation.model_validate(it) for it in raw]

    def token_category(self, category: str, interval: str, limit: Optional[int] = None) -> List[TokenMintInformation]:
        params = tf.shape_query({"limit": limit})
        raw = self.client.get("tokens", f"/{category}/{interval}", params=params)
        return [TokenMintInformation.model_validate(it) for it in raw]

    def token_recent(self) -> List[TokenMintInformation]:
        raw = self.client.get("tokens", "/recent")
        return [TokenMintInformation.model_validate(it) for it in raw]

    # --- Price v3 ---
    def price_v3(self, ids: List[str]) -> Dict[str, PriceItem]:
        raw = self.client.get("price", "", params={"ids": tf.comma_join(ids)})
        return {k: PriceItem.model_validate(v) for k, v in raw.items()}

    # --- Lend/Earn ---
    def earn_deposit(self, body: EarnAmountRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("lend", "/earn/deposit", body.model_dump())
        tx = TransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": tx.model_dump()}
        if simulate and tx.transaction:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def earn_withdraw(self, body: EarnAmountRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("lend", "/earn/withdraw", body.model_dump())
        tx = TransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": tx.model_dump()}
        if simulate and tx.transaction:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def earn_mint(self, body: EarnSharesRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("lend", "/earn/mint", body.model_dump())
        tx = TransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": tx.model_dump()}
        if simulate and tx.transaction:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def earn_redeem(self, body: EarnSharesRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("lend", "/earn/redeem", body.model_dump())
        tx = TransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": tx.model_dump()}
        if simulate and tx.transaction:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(tx.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def earn_deposit_instructions(self, body: EarnAmountRequest) -> InstructionResponse:
        raw = self.client.post("lend", "/earn/deposit-instructions", body.model_dump())
        # Some responses wrap instructions under { instructions: [..] }
        if isinstance(raw, dict) and "instructions" in raw and isinstance(raw["instructions"], list):
            first = raw["instructions"][0] if raw["instructions"] else {}
            return InstructionResponse.model_validate(first)
        return InstructionResponse.model_validate(raw)

    def earn_withdraw_instructions(self, body: EarnAmountRequest) -> InstructionResponse:
        raw = self.client.post("lend", "/earn/withdraw-instructions", body.model_dump())
        if isinstance(raw, dict) and "instructions" in raw and isinstance(raw["instructions"], list):
            first = raw["instructions"][0] if raw["instructions"] else {}
            return InstructionResponse.model_validate(first)
        return InstructionResponse.model_validate(raw)

    def earn_mint_instructions(self, body: EarnSharesRequest) -> InstructionResponse:
        raw = self.client.post("lend", "/earn/mint-instructions", body.model_dump())
        if isinstance(raw, dict) and "instructions" in raw and isinstance(raw["instructions"], list):
            first = raw["instructions"][0] if raw["instructions"] else {}
            return InstructionResponse.model_validate(first)
        return InstructionResponse.model_validate(raw)

    def earn_redeem_instructions(self, body: EarnSharesRequest) -> InstructionResponse:
        raw = self.client.post("lend", "/earn/redeem-instructions", body.model_dump())
        if isinstance(raw, dict) and "instructions" in raw and isinstance(raw["instructions"], list):
            first = raw["instructions"][0] if raw["instructions"] else {}
            return InstructionResponse.model_validate(first)
        return InstructionResponse.model_validate(raw)

    def earn_tokens(self) -> List[TokenInfo]:
        raw = self.client.get("lend", "/earn/tokens")
        fixed: List[Dict[str, Any]] = []
        for it in raw if isinstance(raw, list) else []:
            item = dict(it)
            # Normalize nested asset keys (camelCase -> snake_case) and required fields
            asset = item.get("asset")
            if isinstance(asset, dict):
                a = dict(asset)
                if "chainId" in a and "chain_id" not in a:
                    a["chain_id"] = a.pop("chainId")
                if "logoUrl" in a and "logo_url" not in a:
                    a["logo_url"] = a.pop("logoUrl")
                if "coingeckoId" in a and "coingecko_id" not in a:
                    a["coingecko_id"] = a.pop("coingeckoId")
                item["asset"] = a
            # Normalize liquiditySupplyData numbers -> strings per schema
            lsd = item.get("liquiditySupplyData")
            if isinstance(lsd, dict):
                l = dict(lsd)
                for k, v in list(l.items()):
                    if isinstance(v, (int, float)):
                        l[k] = str(v)
                item["liquiditySupplyData"] = l
            fixed.append(item)
        return [TokenInfo.model_validate(it) for it in fixed]

    def earn_positions(self, users: List[str]) -> List[UserPosition]:
        raw = self.client.get("lend", "/earn/positions", params={"users": tf.comma_join(users)})
        fixed: List[Dict[str, Any]] = []
        for it in raw if isinstance(raw, list) else []:
            item = dict(it)
            token = item.get("token")
            if isinstance(token, dict):
                tok = dict(token)
                asset = tok.get("asset")
                if isinstance(asset, dict):
                    a = dict(asset)
                    if "chainId" in a and "chain_id" not in a:
                        a["chain_id"] = a.pop("chainId")
                    if "logoUrl" in a and "logo_url" not in a:
                        a["logo_url"] = a.pop("logoUrl")
                    if "coingeckoId" in a and "coingecko_id" not in a:
                        a["coingecko_id"] = a.pop("coingeckoId")
                    tok["asset"] = a
                lsd = tok.get("liquiditySupplyData")
                if isinstance(lsd, dict):
                    l = dict(lsd)
                    for k, v in list(l.items()):
                        if isinstance(v, (int, float)):
                            l[k] = str(v)
                    tok["liquiditySupplyData"] = l
                item["token"] = tok
            fixed.append(item)
        return [UserPosition.model_validate(it) for it in fixed]

    def earn_earnings(self, user: str, positions: List[str]) -> UserEarningsResponse:
        raw = self.client.get("lend", "/earn/earnings", params={"user": user, "positions": tf.comma_join(positions)})
        return UserEarningsResponse.model_validate(raw)

    # --- Send API ---
    def send_craft(self, body: CraftSendRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("send", "/craft-send", body.model_dump())
        resp = CraftSendResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate and resp.tx:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.tx, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def send_craft_clawback(self, body: CraftClawbackRequest, simulate: bool = False, simulate_opts: Optional[Dict[str, Any]] = None, network: str = "mainnet") -> Dict[str, Any]:
        raw = self.client.post("send", "/craft-clawback", body.model_dump())
        resp = CraftClawbackResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate and resp.tx:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.tx, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def send_pending_invites(self, address: str, page: Optional[int] = None) -> InviteDataResponse:
        params = tf.shape_query({"address": address, "page": page})
        raw = self.client.get("send", "/pending-invites", params=params)
        return InviteDataResponse.model_validate(raw)

    def send_invite_history(self, address: str, page: Optional[int] = None) -> InviteDataResponse:
        params = tf.shape_query({"address": address, "page": page})
        raw = self.client.get("send", "/invite-history", params=params)
        return InviteDataResponse.model_validate(raw)

    # --- Studio (DBC) ---
    def studio_dbc_create_pool_tx(
        self,
        body: CreateDBCTransactionRequestBody,
        simulate: bool = False,
        simulate_opts: Optional[Dict[str, Any]] = None,
        network: str = "mainnet",
    ) -> Dict[str, Any]:
        raw = self.client.post("studio", "/dbc-pool/create-tx", body.model_dump())
        resp = CreateDBCTransactionResponse.model_validate(raw)
        out: Dict[str, Any] = {"jupiterResponse": resp.model_dump()}
        if simulate and resp.transaction:
            sargs = self._sim_args(simulate_opts)
            sim = self.helius.simulate_transaction(resp.transaction, network=network, **sargs)
            out["simulation"] = sim.model_dump() if hasattr(sim, "model_dump") else sim
        return out

    def studio_dbc_fee_create_tx(
        self,
        body: CreateClaimFeeDBCTransactionRequestBody,
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



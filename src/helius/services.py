from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import HeliusClient
from .schemas import (
    EnhancedTxSummary,
    SignatureInfo,
    TxRawSummary,
    SimulationSummary,
    PriorityFeeSummary,
    AssetsPageSummary,
    AssetSummary,
    TokenAccountsResult,
    AccountInfoSummary,
)
from . import transforms as tf


class HeliusService:
    def __init__(self, client: Optional[HeliusClient] = None):
        self.client = client or HeliusClient()

    # Enhanced REST
    def get_transactions(self, signatures: List[str], network: str = "mainnet") -> List[EnhancedTxSummary]:
        if not signatures:
            raise ValueError("signatures must not be empty")
        if len(signatures) > 100:
            raise ValueError("max 100 signatures per call; chunk your requests")
        url = self.client._enhanced_url("/v0/transactions", network)
        body: Dict[str, Any] = {"transactions": signatures}
        raw = self.client.rest_post(url, body)
        if isinstance(raw, list):
            return [tf.summarize_enhanced_tx(tx) for tx in raw if isinstance(tx, dict)]
        return raw

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
    ) -> List[EnhancedTxSummary]:
        params: Dict[str, Any] = {"limit": limit}
        if tx_type:
            params["type"] = tx_type
        if source:
            params["source"] = source
        if before:
            params["before"] = before
        if until:
            params["until"] = until
        params["commitment"] = commitment or "finalized"

        url = self.client._enhanced_url(f"/v0/addresses/{address}/transactions", network)
        raw = self.client.rest_get(url, params=params)
        if isinstance(raw, list):
            return [tf.summarize_enhanced_tx(tx) for tx in raw if isinstance(tx, dict)]
        return raw

    # RPC
    def get_signatures_for_address(
        self,
        address: str,
        network: str = "mainnet",
        limit: int = 1000,
        before: Optional[str] = None,
        until: Optional[str] = None,
        commitment: Optional[str] = None,
    ) -> List[SignatureInfo]:
        bounded_limit = max(1, min(int(limit), 1000))
        options: Dict[str, Any] = {"limit": bounded_limit}
        if before:
            options["before"] = before
        if until:
            options["until"] = until
        options["commitment"] = commitment or "finalized"
        raw = self.client.rpc(network, "getSignaturesForAddress", [address, options])
        if isinstance(raw, list):
            return [tf.summarize_signature_info(e) for e in raw if isinstance(e, dict)]
        return raw

    def get_transaction_raw(
        self,
        signature: str,
        network: str = "mainnet",
        encoding: str = "jsonParsed",
        commitment: Optional[str] = None,
    ) -> TxRawSummary:
        cfg: Dict[str, Any] = {"encoding": encoding, "maxSupportedTransactionVersion": 0}
        cfg["commitment"] = commitment or "finalized"
        raw = self.client.rpc(network, "getTransaction", [signature, cfg])
        if isinstance(raw, dict) and (raw.get("meta") or raw.get("transaction")):
            return tf.summarize_raw_transaction(raw)
        return raw

    def simulate_transaction(
        self,
        transaction: str,
        network: str = "mainnet",
        sig_verify: bool = False,
        commitment: Optional[str] = None,
    ) -> SimulationSummary:
        cfg: Dict[str, Any] = {"encoding": "base64", "sigVerify": sig_verify}
        if commitment:
            cfg["commitment"] = commitment
        raw = self.client.rpc(network, "simulateTransaction", [transaction, cfg])
        if isinstance(raw, dict):
            return tf.summarize_simulation(raw)
        return raw

    def get_priority_fee_estimate(
        self,
        network: str = "mainnet",
        transaction: Optional[str] = None,
        account_keys: Optional[List[str]] = None,
        priority_level: Optional[str] = None,
    ) -> PriorityFeeSummary:
        if transaction and account_keys:
            raise ValueError("Provide either transaction or account_keys, not both.")
        body: Dict[str, Any] = {}
        if transaction:
            body["transaction"] = transaction
        if account_keys:
            body["accountKeys"] = account_keys
        options: Dict[str, Any] = {"recommended": True}
        if priority_level:
            options["priorityLevel"] = priority_level
        body["options"] = options
        result = self.client.rpc(network, "getPriorityFeeEstimate", [body])
        if isinstance(result, dict):
            return tf.summarize_priority_fee(result)
        return {"micro_lamports": int(result)} if isinstance(result, (int, str)) else result

    # DAS
    def get_asset(self, asset_id: str, network: str = "mainnet") -> AssetSummary:
        raw = self.client.rpc(network, "getAsset", {"id": asset_id})
        if isinstance(raw, dict):
            return tf.summarize_asset(raw)
        return raw

    def get_assets_by_owner(
        self,
        owner_address: str,
        page: int = 1,
        limit: int = 50,
        network: str = "mainnet",
        show_fungible: bool = False,
        show_native_balance: bool = False,
        show_zero_balance: bool = False,
    ) -> AssetsPageSummary:
        params: Dict[str, Any] = {
            "ownerAddress": owner_address,
            "page": page,
            "limit": limit,
            "displayOptions": {
                "showFungible": show_fungible,
                "showNativeBalance": show_native_balance,
                "showZeroBalance": show_zero_balance,
            },
        }
        raw = self.client.rpc(network, "getAssetsByOwner", params)
        if isinstance(raw, dict):
            return tf.summarize_assets_page(raw)
        return raw

    def search_assets(
        self,
        network: str = "mainnet",
        owner_address: Optional[str] = None,
        token_type: str = "all",
        creator_address: Optional[str] = None,
        collection: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
        limit: int = 50,
        page: int = 1,
    ) -> AssetsPageSummary:
        params: Dict[str, Any] = {"limit": limit, "page": page}
        # Only include tokenType if not the default 'all' to avoid validation requiring owner_address
        if token_type and token_type != "all":
            params["tokenType"] = token_type
        if owner_address:
            params["ownerAddress"] = owner_address
        if creator_address:
            params["creatorAddress"] = creator_address
        if collection:
            params["grouping"] = ["collection", collection]
        if attributes:
            traits_list: List[Dict[str, Any]] = []
            for trait_type, value in attributes.items():
                values_list = value if isinstance(value, list) else [value]
                traits_list.append({"trait_type": trait_type, "values": values_list})
            params["traits"] = traits_list
        raw = self.client.rpc(network, "searchAssets", params)
        if isinstance(raw, dict):
            return tf.summarize_assets_page(raw)
        return raw

    def get_token_accounts(self, owner: str, mint: Optional[str] = None, network: str = "mainnet") -> TokenAccountsResult:
        params: Dict[str, Any] = {"ownerAddress": owner}
        if mint:
            params["mint"] = mint
        raw = self.client.rpc(network, "getTokenAccounts", params)
        if isinstance(raw, dict):
            return tf.summarize_token_accounts(raw)
        return raw

    # Small helpers
    def get_balance(self, public_key: str, network: str = "mainnet", commitment: Optional[str] = None) -> int:
        params: List[Any] = [public_key]
        params.append({"commitment": commitment or "finalized"})
        result = self.client.rpc(network, "getBalance", params)
        if isinstance(result, dict) and "value" in result:
            return int(result.get("value"))
        return int(result)

    def get_account_info(self, address: str, network: str = "mainnet", encoding: str = "base64") -> AccountInfoSummary:
        raw = self.client.rpc(network, "getAccountInfo", [address, {"encoding": encoding, "commitment": "finalized"}])
        if isinstance(raw, dict):
            value = raw.get("value") or {}
            if isinstance(value, dict):
                return tf.summarize_account_info(value)
        return raw



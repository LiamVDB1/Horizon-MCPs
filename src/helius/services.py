from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio

from .client import HeliusClient
from .schemas import (
    EnhancedTxSummary,
    SignatureInfo,
    SignatureStatus,
    TxRawSummary,
    SimulationSummary,
    PriorityFeeSummary,
    AssetsPageSummary,
    AssetSummary,
    TokenAccountsResult,
    AccountInfoSummary,
    ProgramAccountSummary,
    TokenLargestAccountItem,
)
from . import transforms as tf


class HeliusService:
    def __init__(self, client: Optional[HeliusClient] = None):
        self.client = client or HeliusClient()

    # Enhanced REST
    #TODO CHECK
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

    #TODO CHECK
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

    #TODO Enhance
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
        cfg: Dict[str, Any] = {"encoding": "base64", "sigVerify": sig_verify, "replaceRecentBlockhash": True}
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
        params: Dict[str, Any] = {"owner": owner}
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

    # New RPC helpers
    #TODO CHECK
    def get_signature_statuses(
        self,
        signatures: List[str],
        network: str = "mainnet",
        search_transaction_history: bool = False,
        commitment: Optional[str] = None,
    ) -> List[Optional[SignatureStatus]]:
        if not signatures:
            raise ValueError("signatures must not be empty")
        opts: Dict[str, Any] = {"searchTransactionHistory": bool(search_transaction_history)}
        if commitment:
            opts["commitment"] = commitment
        res = self.client.rpc(network, "getSignatureStatuses", [signatures, opts])
        if isinstance(res, dict):
            values = res.get("value") or []
            out: List[Optional[SignatureStatus]] = []
            for v in values:
                out.append(tf.summarize_signature_status(v) if isinstance(v, (dict,)) or v is None else None)
            return out
        return res

    #TODO CHECK
    def get_multiple_accounts(
        self,
        pubkeys: List[str],
        network: str = "mainnet",
        encoding: str = "jsonParsed",
        commitment: Optional[str] = None,
        data_slice: Optional[Dict[str, int]] = None,
        min_context_slot: Optional[int] = None,
        changed_since_slot: Optional[int] = None,
    ) -> List[Optional[AccountInfoSummary]]:
        if not pubkeys:
            raise ValueError("pubkeys must not be empty")
        cfg: Dict[str, Any] = {"encoding": encoding}
        if commitment:
            cfg["commitment"] = commitment
        else:
            cfg["commitment"] = "finalized"
        if isinstance(data_slice, dict):
            cfg["dataSlice"] = data_slice
        if isinstance(min_context_slot, int):
            cfg["minContextSlot"] = min_context_slot
        if isinstance(changed_since_slot, int):
            cfg["changedSinceSlot"] = changed_since_slot
        res = self.client.rpc(network, "getMultipleAccounts", [pubkeys, cfg])
        if isinstance(res, dict):
            return tf.summarize_multiple_accounts(res)
        return res

    #TODO CHECK
    def get_program_accounts(
        self,
        program_id: str,
        network: str = "mainnet",
        encoding: str = "base64",
        filters: Optional[List[Dict[str, Any]]] = None,
        data_slice: Optional[Dict[str, int]] = None,
        commitment: Optional[str] = None,
        changed_since_slot: Optional[int] = None,
    ) -> List[ProgramAccountSummary]:
        opts: Dict[str, Any] = {"encoding": encoding}
        if commitment:
            opts["commitment"] = commitment
        else:
            opts["commitment"] = "finalized"
        if filters:
            opts["filters"] = filters
        if data_slice:
            opts["dataSlice"] = data_slice
        if isinstance(changed_since_slot, int):
            opts["changedSinceSlot"] = changed_since_slot
        res = self.client.rpc(network, "getProgramAccounts", [program_id, opts])
        if isinstance(res, list):
            out: List[ProgramAccountSummary] = []
            for it in res:
                if isinstance(it, dict):
                    out.append(tf.summarize_program_account(it))
            return out
        return res

    def get_token_largest_accounts(
        self,
        mint: str,
        network: str = "mainnet",
        commitment: Optional[str] = None,
    ) -> List[TokenLargestAccountItem]:
        params: List[Any] = [mint]
        if commitment:
            params.append({"commitment": commitment})
        res = self.client.rpc(network, "getTokenLargestAccounts", params)
        if isinstance(res, dict):
            return tf.summarize_token_largest_accounts(res)
        return res

    def get_token_whale_addresses(
        self,
        mint: str,
        network: str = "mainnet",
        min_amount_ui: float = 1000.0,
        min_sol_balance: float = 0.1,
    ) -> Optional[(str, Optional[float])]:
        """
        Get a single address of a token "whale" (large holder) for simulation purposes.
        
        This method is designed for Jupiter API use cases where you need a "taker" 
        with guaranteed sufficient funds to simulate transactions.
        
        First tries getTokenLargestAccounts, then falls back to DAS getTokenAccounts 
        pagination for large tokens like USDC/SOL/USDT that have too many accounts.
        
        Args:
            mint: Token mint address
            network: Network ("mainnet" or "devnet")
            min_amount_ui: Minimum token amount (adjusted for decimals)
            min_sol_balance: Minimum SOL balance for transaction fees (in SOL)
            
        Returns:
            A single address that meets the whale criteria, or None if not found
        """
        SOL = "So11111111111111111111111111111111111111112"
        known_failures = [
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", # USDC
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB" # USDT
        ]

        if mint == SOL:
            whale_acc = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM" # Binance Hot Wallet
            whale_bal = self.get_balance(whale_acc, network) - 100 # 100 Sol as buffer (fee etc)
            return whale_acc if min_amount_ui <= whale_bal else (whale_acc, whale_bal)


        if mint in known_failures:
            return self._get_whales_via_das_pagination(mint, network, min_amount_ui, min_sol_balance)
        
        # First try the standard RPC method
        try:                        
            largest = self.get_token_largest_accounts(mint, network)
            if largest and len(largest) > 0:
                for account in largest:
                    if account.address and account.ui_amount_string:
                        try:
                            amount = float(account.ui_amount_string)
                            if amount >= min_amount_ui:
                                sol_balance = self.get_balance(account.address, network)
                                sol_amount = sol_balance / 1_000_000_000
                                if sol_amount >= min_sol_balance:
                                    return account.address
                        except (ValueError, TypeError):
                            continue
                    
        except RuntimeError as e:
            if "Too many accounts" not in str(e) and "Request deprioritized" not in str(e):
                raise  # Re-raise unexpected errors
            # Fall through to DAS method for large tokens
        
        # Fallback: Use DAS getTokenAccounts with pagination
        return self._get_whales_via_das_pagination(
            mint, network, min_amount_ui, min_sol_balance
        )
    
    def _get_whales_via_das_pagination(
        self,
        mint: str,
        network: str,
        min_amount_ui: float,
        min_sol_balance: float,
    ) -> Optional[(str, Optional[float])]:
        """
        Find a whale address using DAS getTokenAccounts with pagination.
        Returns early once a suitable address is found.
        """
        limit = 1000  # DAS max per page
        cursor: Optional[str] = None
        iterations = 0
        max_iterations = 2  # Only check first 2 pages for performance (min_amount_ui would just be unreasonable)

        # Default decimals for common fungible tokens
        decimals = self.get_asset(mint, network).decimals or 6

        largest_candidate = None
        largest_amount = 0.0

        while iterations < max_iterations:
            iterations += 1
            try:
                params: Dict[str, Any] = {"mint": mint, "limit": limit}
                if cursor:
                    params["cursor"] = cursor

                das_result = self.client.rpc(network, "getTokenAccounts", params)
                # Validate against DAS schema for consistency
                try:
                    raw = tf.RawDasTokenAccountsResult.model_validate(das_result)  # type: ignore[attr-defined]
                except Exception:
                    # Fallback to dict-parsing if validation fails
                    raw = None

                if raw is not None:
                    token_accounts = raw.token_accounts or []
                else:
                    if not isinstance(das_result, dict):
                        break
                    token_accounts = das_result.get("token_accounts") or []
                    if not isinstance(token_accounts, list) or not token_accounts:
                        break

                # Build candidate owners from this page and track largest
                candidate_owners: List[str] = []
                for it in token_accounts:                    
                    try:
                        # Support both validated model and dict
                        if hasattr(it, "owner"):
                            owner = it.owner
                            amount_raw = it.amount
                        else:
                            owner = it.get("owner") if isinstance(it, dict) else None
                            amount_raw = it.get("amount") if isinstance(it, dict) else None

                        if not owner or amount_raw is None:
                            continue

                        amount_ui = float(amount_raw) / (10 ** decimals)
                        
                        # Track the largest candidate regardless of threshold
                        if amount_ui > largest_amount:
                            largest_amount = amount_ui
                            largest_candidate = owner

                        if amount_ui >= min_amount_ui:
                            print(f"{amount_raw} - {owner} - {amount_ui}")
                            candidate_owners.append(owner)
                    except Exception:
                        continue

                # Concurrently check balances with a semaphore and exit on first hit
                if candidate_owners:
                    threshold_lamports = int(min_sol_balance * 1_000_000_000)
                    semaphore = 5

                    print(f"found {len(candidate_owners) } candidate_owners")
                    print(f"candidate owners: {candidate_owners}")

                    async def _first_owner(owners: List[str]) -> Optional[str]:
                        sem = asyncio.Semaphore(semaphore)

                        async def _check(owner: str) -> Optional[str]:
                            async with sem:
                                try:
                                    lamports = await asyncio.to_thread(self.get_balance, owner, network)
                                except Exception:
                                    return None
                                return owner if (lamports or 0) >= threshold_lamports else None

                        tasks = [asyncio.create_task(_check(o)) for o in owners]
                        for coro in asyncio.as_completed(tasks):
                            try:
                                res = await coro
                            except Exception:
                                continue
                            if res:
                                # Cancel all other tasks
                                for t in tasks:
                                    if not t.done():
                                        t.cancel()

                                # Return the first result
                                return res
                        return None

                    found = asyncio.run(_first_owner(candidate_owners))
                    if found:
                        return found

                # Advance cursor; if no cursor returned, stop
                cursor = (raw.cursor if raw is not None else das_result.get("cursor")) if isinstance(das_result, dict) or raw is not None else None
                if not cursor:
                    break
            except Exception:
                break

        # If no qualifying candidate found, return the largest one we found
        if largest_candidate:
            print(f"Found no valid ui_amount, falling back to largest: {largest_amount}")
            try:
                sol_lamports = self.get_balance(largest_candidate, network)
                sol_amount = (sol_lamports or 0) / 1_000_000_000
                if sol_amount >= min_sol_balance:
                    return largest_candidate, largest_amount
            except Exception:
                pass

        return None
    



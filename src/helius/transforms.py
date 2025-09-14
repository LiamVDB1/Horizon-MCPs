from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    EnhancedTxSummary,
    NativeTransfer,
    TokenTransfer,
    SignatureInfo,
    SignatureStatus,
    TxRawSummary,
    SimulationSummary,
    PriorityFeeSummary,
    PriorityFeeLevels,
    AssetSummary,
    AssetsPageSummary,
    TokenAccountsResult,
    TokenAccountSummary,
    AccountInfoSummary,
    ProgramAccountSummary,
    RawEnhancedTransaction,
    RawSignatureForAddressItem,
    RawGetTransaction,
    RawSimulateTransactionResponse,
    RawPriorityFeeEstimate,
    RawDasAsset,
    RawDasAssetsPage,
    RawDasTokenAccountsResult,
    RawGetBalanceResult,
    RawGetAccountInfoResult,
    RawAccountInfoValue,
    RawSignatureStatus,
    RawGetSignatureStatusesResult,
    RawGetMultipleAccountsResult,
    RawProgramAccount,
    RawTokenLargestAccounts,
    RawTokenLargestAccountItem,
    TokenLargestAccountItem,
)


def summarize_enhanced_tx(tx: Dict[str, Any]) -> EnhancedTxSummary:
    raw = RawEnhancedTransaction.model_validate(tx)

    signature = raw.signature
    slot = raw.slot
    timestamp = raw.timestamp
    tx_type = raw.type
    source = raw.source
    fee = raw.fee
    transaction_error = raw.transaction_error

    succeeded: Optional[bool] = None
    status = raw.status if raw.status is not None else raw.transaction_error
    if status is not None:
        if isinstance(status, str):
            succeeded = status.lower() == "success"
        elif isinstance(status, dict):
            # Heuristics: consider InstructionError/err keys as failure
            succeeded = (status.get("InstructionError") is None) and (status.get("err") is None)

    native_transfers: List[NativeTransfer] = []
    for nt in raw.native_transfers or []:
        try:
            native_transfers.append(
                NativeTransfer(
                    from_addr=(nt.from_user_account or nt.from_ or ""),
                    to_addr=(nt.to_user_account or nt.to_ or ""),
                    amount_lamports=int(nt.amount or 0),
                )
            )
        except Exception:
            continue

    token_transfers: List[TokenTransfer] = []
    for tt in raw.token_transfers or []:
        # amount might be string/int or object with amount field
        amount_str: str = ""
        if isinstance(tt.token_amount, dict):
            val = tt.token_amount.get("amount")
            amount_str = str(val) if val is not None else ""
        elif isinstance(tt.token_amount, (int, str, float)):
            amount_str = str(tt.token_amount)

        decimals_val: Optional[int] = None
        if isinstance(tt.decimals, int):
            decimals_val = tt.decimals
        elif isinstance(tt.token_amount, dict):
            d2 = tt.token_amount.get("decimals")
            try:
                if d2 is not None:
                    decimals_val = int(d2)
            except Exception:
                decimals_val = None

        token_transfers.append(
            TokenTransfer(
                mint=tt.mint or "",
                from_addr=(tt.from_user_account or tt.from_token_account or tt.from_ or ""),
                to_addr=(tt.to_user_account or tt.to_token_account or tt.to_ or ""),
                amount=amount_str,
                decimals=decimals_val,
            )
        )

    return EnhancedTxSummary(
        signature=signature,
        slot=slot,
        timestamp=timestamp,
        type=tx_type,
        source=source,
        fee_lamports=fee,
        succeeded=succeeded,
        transaction_error=transaction_error,
        native_transfers=native_transfers,
        token_transfers=token_transfers,
    )


def summarize_signature_info(entry: Dict[str, Any]) -> SignatureInfo:
    raw = RawSignatureForAddressItem.model_validate(entry)
    return SignatureInfo(
        signature=raw.signature,
        slot=raw.slot,
        block_time=raw.blockTime,
        confirmation_status=raw.confirmationStatus,
        err=raw.err,
    )


def _extract_program_ids_from_transaction(tx: Dict[str, Any]) -> List[str]:
    program_ids: List[str] = []
    try:
        parsed = RawGetTransaction.model_validate(tx)
        if not (parsed.transaction and parsed.transaction.message):
            return []

        for ix in parsed.transaction.message.instructions:
            pid_index = ix.programIdIndex
            if isinstance(pid_index, int): # Indexed account
                if not parsed.transaction.message.accountKeys or pid_index >= len(parsed.transaction.message.accountKeys):
                    continue                        
                account_key = parsed.transaction.message.accountKeys[pid_index]
                if hasattr(account_key, 'pubkey'):
                    program_ids.append(account_key.pubkey)
                elif isinstance(account_key, str):
                    program_ids.append(account_key)

        # Deduplicate while preserving order
        seen = set()
        unique: List[str] = []
        for pid in program_ids:
            if pid not in seen:
                unique.append(pid)
                seen.add(pid)            
        return unique
    except Exception:
        return []


def summarize_raw_transaction(tx: Dict[str, Any]) -> TxRawSummary:
    parsed = RawGetTransaction.model_validate(tx)
    meta = parsed.meta or None
    logs = (meta.logMessages if meta else None) or []
    if isinstance(logs, list) and len(logs) > 30:
        logs = logs[:15] + ["... (truncated) ..."] + logs[-14:]
    sig = None
    if parsed.transaction and parsed.transaction.signatures:
        sig = parsed.transaction.signatures[0] if parsed.transaction.signatures else None
    return TxRawSummary(
        signature=sig,
        slot=parsed.slot,
        block_time=parsed.blockTime,
        fee_lamports=(meta.fee if meta else None),        
        err=(meta.err if meta else None),
        program_ids=_extract_program_ids_from_transaction(tx),
        log_messages=logs if isinstance(logs, list) else [],
    )


def summarize_simulation(res: Dict[str, Any]) -> SimulationSummary:
    parsed = RawSimulateTransactionResponse.model_validate(res)
    value = parsed.value
    if not value:
        return SimulationSummary(err=None, units_consumed=None, logs=[])
    logs = value.logs or []
    if isinstance(logs, list) and len(logs) > 50:
        logs = logs[:25] + ["... (truncated) ..."] + logs[-24:]
    return SimulationSummary(
        err=value.err,
        units_consumed=value.unitsConsumed,
        logs=logs if isinstance(logs, list) else [],
    )


def summarize_priority_fee(result: Dict[str, Any]) -> PriorityFeeSummary:
    parsed = RawPriorityFeeEstimate.model_validate(result)
    levels: Optional[PriorityFeeLevels] = None
    if parsed.priorityFeeLevels:
        levels = PriorityFeeLevels(
            min=parsed.priorityFeeLevels.min,
            low=parsed.priorityFeeLevels.low,
            medium=parsed.priorityFeeLevels.medium,
            high=parsed.priorityFeeLevels.high,
            veryHigh=parsed.priorityFeeLevels.veryHigh,
            unsafeMax=parsed.priorityFeeLevels.unsafeMax,
        )
    return PriorityFeeSummary(
        estimated_micro_lamports=int(parsed.priorityFeeEstimate or 0),
        levels=levels,
    )


def _first_file_image(asset: Dict[str, Any]) -> Optional[str]:
    content = asset.get("content") or {}
    files = content.get("files") or []
    if isinstance(files, list) and files:
        uri = files[0].get("uri") if isinstance(files[0], dict) else None
        if isinstance(uri, str):
            return uri
    links = content.get("links") or {}
    if isinstance(links, dict):
        img = links.get("image") or links.get("img")
        if isinstance(img, str):
            return img
    return None


def _extract_collection(asset: Dict[str, Any]) -> Optional[str]:
    grouping = asset.get("grouping") or []
    if isinstance(grouping, list):
        for g in grouping:
            if isinstance(g, dict) and g.get("group_key") == "collection":
                return g.get("group_value")
            if isinstance(g, dict) and g.get("group_key") == "collectionId":
                return g.get("group_value")
    return None


def _extract_owner(asset: Dict[str, Any]) -> Optional[str]:
    ownership = asset.get("ownership") or {}
    owner = ownership.get("owner") if isinstance(ownership, dict) else None
    if isinstance(owner, str):
        return owner
    return None


def _extract_name_symbol(asset: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    content = asset.get("content") or {}
    meta = content.get("metadata") or {}
    name = meta.get("name") if isinstance(meta, dict) else None
    symbol = meta.get("symbol") if isinstance(meta, dict) else None
    if not isinstance(name, str):
        name = None
    if not isinstance(symbol, str):
        symbol = None
    return name, symbol


def _extract_token_price(asset: Dict[str, Any]) -> Optional[float]:
    token_info = asset.get("token_info") or {}
    if not isinstance(token_info, dict):
        return None
    price_info = token_info.get("price_info") or {}
    if isinstance(price_info, dict):
        for key in ("price", "current", "price_per_token", "usd"):
            val = price_info.get(key)
            if isinstance(val, (int, float)):
                return float(val)
    return None


def summarize_asset(asset: Dict[str, Any]) -> AssetSummary:
    parsed = RawDasAsset.model_validate(asset)
    # Name and symbol
    name = None
    symbol = None
    if parsed.content and parsed.content.metadata:
        name = parsed.content.metadata.name
        symbol = parsed.content.metadata.symbol
    # Image
    image = None
    if parsed.content:
        if parsed.content.files:
            first = parsed.content.files[0]
            if isinstance(first, dict):
                image = first.get("uri")  # keep compatibility fallback
            else:
                image = first.uri
        if not image and parsed.content.links:
            image = parsed.content.links.image
    # Owner
    owner = parsed.ownership.owner if parsed.ownership else None
    # Collection
    collection = None
    for g in parsed.grouping or []:
        if (g.group_key == "collection" or g.group_key == "collectionId") and g.group_value:
            collection = g.group_value
            break    
        

    return AssetSummary(
        id=parsed.id,
        name=name,
        symbol=symbol,
        image=image,
        owner=owner,
        collection=collection,
        compressed=bool(parsed.compression.compressed) if parsed.compression else False,
        interface=parsed.interface,
    )


def summarize_assets_page(result: Dict[str, Any]) -> AssetsPageSummary:
    parsed = RawDasAssetsPage.model_validate(result)
    items: List[AssetSummary] = []
    for it in parsed.items or []:
        # RawDasAsset -> dict for reuse of summarize_asset
        items.append(summarize_asset(it.model_dump(by_alias=True)))
    native_balance = parsed.nativeBalance if parsed.nativeBalance is not None else parsed.native_balance
    native_lamports: Optional[int] = None
    if isinstance(native_balance, dict):
        lamports = native_balance.get("lamports") or native_balance.get("amount")
        try:
            if lamports is not None:
                native_lamports = int(lamports)
        except Exception:
            native_lamports = None
    elif isinstance(native_balance, (int, str)):
        try:
            native_lamports = int(native_balance)
        except Exception:
            native_lamports = None
    return AssetsPageSummary(
        total=parsed.total,
        items=items,
        native_balance_lamports=native_lamports,
    )


def summarize_token_accounts(result: Dict[str, Any]) -> TokenAccountsResult:
    parsed = RawDasTokenAccountsResult.model_validate(result)
    out_items: List[TokenAccountSummary] = []
    for it in parsed.items or []:
        token_account = it.token_account or it.address or it.id
        owner = it.owner or it.ownerAddress
        mint = it.mint
        amount: Optional[str] = None
        decimals: Optional[int] = None
        ui_amount_str: Optional[str] = None
        if it.balance:
            amount = str(it.balance.amount) if it.balance.amount is not None else None
            decimals = it.balance.decimals
            ui_amount_str = it.balance.uiAmountString
        elif it.amount is not None:
            amount = str(it.amount)
        out_items.append(
            TokenAccountSummary(
                token_account=token_account,
                owner=owner,
                mint=mint,
                amount=amount,
                decimals=decimals,
                ui_amount_string=ui_amount_str,
            )
        )
    return TokenAccountsResult(total=parsed.total, items=out_items)


def summarize_account_info(value: Dict[str, Any]) -> AccountInfoSummary:
    raw = RawAccountInfoValue.model_validate(value)
    return AccountInfoSummary(
        lamports=int(raw.lamports or 0),
        owner=raw.owner or "",
        executable=bool(raw.executable or False),
        rent_epoch=int(raw.rentEpoch or 0),
        space=raw.space,
    )


def summarize_signature_status(entry: Optional[Dict[str, Any]]) -> Optional[SignatureStatus]:
    if entry is None:
        return None
    raw = RawSignatureStatus.model_validate(entry)
    return SignatureStatus(
        slot=raw.slot,
        confirmations=raw.confirmations,
        err=raw.err,
        status=raw.status,
        confirmation_status=raw.confirmationStatus,
    )


def summarize_multiple_accounts(result: Dict[str, Any]) -> List[Optional[AccountInfoSummary]]:
    parsed = RawGetMultipleAccountsResult.model_validate(result)
    out: List[Optional[AccountInfoSummary]] = []
    for v in (parsed.value or []):
        if v is None:
            out.append(None)
        elif isinstance(v, dict):
            try:
                # v can be RawAccountInfoValue or RawAccountStaticValue; only summarize the former
                if "lamports" in v:
                    out.append(summarize_account_info(v))
                else:
                    out.append(None)
            except Exception:
                out.append(None)
        else:
            try:
                # v is a pydantic object (RawAccountInfoValue or RawAccountStaticValue)
                if hasattr(v, 'lamports') and v.lamports is not None:
                    # Convert pydantic object to dict for summarize_account_info
                    out.append(summarize_account_info(v.model_dump(by_alias=True)))
                else:
                    out.append(None)
            except Exception:
                out.append(None)
    return out


def summarize_program_account(entry: Dict[str, Any]) -> ProgramAccountSummary:
    raw = RawProgramAccount.model_validate(entry)
    account_summary = summarize_account_info(raw.account.model_dump(by_alias=True))
    return ProgramAccountSummary(pubkey=raw.pubkey, account=account_summary)


def summarize_token_largest_accounts(result: Dict[str, Any]) -> List[TokenLargestAccountItem]:
    parsed = RawTokenLargestAccounts.model_validate(result)
    items: List[TokenLargestAccountItem] = []
    for it in parsed.value or []:
        items.append(
            TokenLargestAccountItem(
                address=it.address,
                amount=it.amount,
                decimals=it.decimals,
                ui_amount_string=it.uiAmountString,
            )
        )
    return items


from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    EnhancedTxSummary,
    NativeTransfer,
    TokenTransfer,
    SignatureInfo,
    TxRawSummary,
    SimulationSummary,
    PriorityFeeSummary,
    PriorityFeeLevels,
    AssetSummary,
    AssetsPageSummary,
    TokenAccountsResult,
    TokenAccountSummary,
    AccountInfoSummary,
)


def summarize_enhanced_tx(tx: Dict[str, Any]) -> EnhancedTxSummary:
    signature = tx.get("signature")
    slot = tx.get("slot")
    timestamp = tx.get("timestamp")
    tx_type = tx.get("type")
    source = tx.get("source")
    fee = tx.get("fee")

    succeeded: Optional[bool] = None
    status = tx.get("status") or tx.get("transactionError")
    if status is not None:
        if isinstance(status, str):
            succeeded = status.lower() == "success"
        elif isinstance(status, dict):
            succeeded = status.get("InstructionError") is None and status.get("err") is None

    native_transfers: List[NativeTransfer] = []
    for nt in tx.get("nativeTransfers", []) or []:
        try:
            native_transfers.append(NativeTransfer(
                from_addr=nt.get("fromUserAccount") or nt.get("from") or "",
                to_addr=nt.get("toUserAccount") or nt.get("to") or "",
                amount_lamports=int(nt.get("amount", 0)),
            ))
        except Exception:
            continue

    token_transfers: List[TokenTransfer] = []
    for tt in tx.get("tokenTransfers", []) or []:
        amount_val = tt.get("tokenAmount", "")
        amount_str = str(amount_val if amount_val is not None else "")
        decimals_val: Optional[int] = None
        dv = tt.get("decimals")
        if isinstance(dv, int):
            decimals_val = dv
        else:
            ta = tt.get("tokenAmount")
            if isinstance(ta, dict):
                d2 = ta.get("decimals")
                try:
                    if d2 is not None:
                        decimals_val = int(d2)
                except Exception:
                    decimals_val = None
        t = TokenTransfer(
            mint=tt.get("mint") or "",
            from_addr=tt.get("fromUserAccount") or tt.get("fromTokenAccount") or tt.get("from") or "",
            to_addr=tt.get("toUserAccount") or tt.get("toTokenAccount") or tt.get("to") or "",
            amount=amount_str,
            decimals=decimals_val,
        )
        token_transfers.append(t)

    return EnhancedTxSummary(
        signature=signature,
        slot=slot,
        timestamp=timestamp,
        type=tx_type,
        source=source,
        fee_lamports=fee,
        succeeded=succeeded,
        native_transfers=native_transfers,
        token_transfers=token_transfers,
    )


def summarize_signature_info(entry: Dict[str, Any]) -> SignatureInfo:
    return SignatureInfo(
        signature=entry.get("signature"),
        slot=entry.get("slot"),
        block_time=entry.get("blockTime"),
        confirmation_status=entry.get("confirmationStatus"),
        err=entry.get("err"),
    )


def _extract_program_ids_from_transaction(tx: Dict[str, Any]) -> List[str]:
    program_ids: List[str] = []
    try:
        message = (tx.get("transaction") or {}).get("message") or {}
        instructions = message.get("instructions", []) or []
        for ix in instructions:
            pid = ix.get("programId") or ix.get("programIdIndex")
            if isinstance(pid, str):
                program_ids.append(pid)
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
    meta = tx.get("meta") or {}
    logs = meta.get("logMessages") or []
    if isinstance(logs, list) and len(logs) > 30:
        logs = logs[:15] + ["... (truncated) ..."] + logs[-14:]
    return TxRawSummary(
        signature=(tx.get("transaction") or {}).get("signatures", [None])[0],
        slot=tx.get("slot"),
        block_time=tx.get("blockTime"),
        fee_lamports=meta.get("fee"),
        compute_units_consumed=meta.get("computeUnitsConsumed"),
        err=meta.get("err"),
        program_ids=_extract_program_ids_from_transaction(tx),
        log_messages=logs if isinstance(logs, list) else [],
    )


def summarize_simulation(res: Dict[str, Any]) -> SimulationSummary:
    value = res.get("value") if isinstance(res, dict) else None
    if not isinstance(value, dict):
        return SimulationSummary(err=None, units_consumed=None, logs=[])
    logs = value.get("logs") or []
    if isinstance(logs, list) and len(logs) > 50:
        logs = logs[:25] + ["... (truncated) ..."] + logs[-24:]
    return SimulationSummary(
        err=value.get("err"),
        units_consumed=value.get("unitsConsumed"),
        logs=logs if isinstance(logs, list) else [],
    )


def summarize_priority_fee(result: Dict[str, Any]) -> PriorityFeeSummary:
    levels_raw = result.get("priorityFeeLevels") or {}
    levels: Optional[PriorityFeeLevels] = None
    if isinstance(levels_raw, dict) and levels_raw:
        keep_keys = ["min", "low", "medium", "high", "veryHigh", "unsafeMax"]
        levels = PriorityFeeLevels(**{k: int(levels_raw[k]) for k in keep_keys if k in levels_raw})
    return PriorityFeeSummary(
        micro_lamports=int(result.get("priorityFeeEstimate", 0)),
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
    name, symbol = _extract_name_symbol(asset)
    return AssetSummary(
        id=asset.get("id"),
        name=name,
        symbol=symbol,
        image=_first_file_image(asset),
        owner=_extract_owner(asset),
        collection=_extract_collection(asset),
        compressed=bool((asset.get("compression") or {}).get("compressed", False)),
        interface=asset.get("interface"),
        token_price_usd=_extract_token_price(asset),
    )


def summarize_assets_page(result: Dict[str, Any]) -> AssetsPageSummary:
    items_raw = result.get("items") or []
    items: List[AssetSummary] = []
    if isinstance(items_raw, list):
        for it in items_raw:
            if isinstance(it, dict):
                items.append(summarize_asset(it))
    native_balance = result.get("nativeBalance") or result.get("native_balance")
    if isinstance(native_balance, dict):
        lamports = native_balance.get("lamports") or native_balance.get("amount")
        native_lamports = int(lamports) if isinstance(lamports, (int, str)) and str(lamports).isdigit() else None
    elif isinstance(native_balance, (int, str)):
        native_lamports = int(native_balance)
    else:
        native_lamports = None
    return AssetsPageSummary(
        total=result.get("total"),
        items=items,
        native_balance_lamports=native_lamports,
    )


def summarize_token_accounts(result: Dict[str, Any]) -> TokenAccountsResult:
    items_in = result.get("items") or result.get("token_accounts") or []
    out_items: List[TokenAccountSummary] = []
    if isinstance(items_in, list):
        for it in items_in:
            if not isinstance(it, dict):
                continue
            token_account = it.get("token_account") or it.get("address") or it.get("id")
            owner = it.get("owner") or it.get("ownerAddress")
            mint = it.get("mint")
            amount = None
            decimals = None
            ui_amount_str = None
            bal = it.get("balance") or it.get("amount")
            if isinstance(bal, dict):
                amount = str(bal.get("amount")) if bal.get("amount") is not None else None
                decimals = bal.get("decimals")
                ui_amount_str = bal.get("uiAmountString") or bal.get("ui_amount_string")
            elif isinstance(bal, (str, int)):
                amount = str(bal)
            out_items.append(TokenAccountSummary(
                token_account=token_account,
                owner=owner,
                mint=mint,
                amount=amount,
                decimals=decimals,
                ui_amount_string=ui_amount_str,
            ))
    return TokenAccountsResult(total=result.get("total"), items=out_items)


def summarize_account_info(value: Dict[str, Any]) -> AccountInfoSummary:
    return AccountInfoSummary(
        lamports=int(value.get("lamports", 0)),
        owner=value.get("owner"),
        executable=bool(value.get("executable", False)),
        rent_epoch=int(value.get("rentEpoch", 0)),
        space=value.get("space"),
    )



from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class _BaseModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class NativeTransfer(_BaseModel):
    from_addr: str
    to_addr: str
    amount_lamports: int


class TokenTransfer(_BaseModel):
    mint: str
    from_addr: str
    to_addr: str
    amount: str
    decimals: Optional[int] = None


class EnhancedTxSummary(_BaseModel):
    signature: Optional[str] = None
    slot: Optional[int] = None
    timestamp: Optional[int] = None
    type: Optional[str] = None
    source: Optional[str] = None
    fee_lamports: Optional[int] = None
    succeeded: Optional[bool] = None
    native_transfers: List[NativeTransfer] = Field(default_factory=list)
    token_transfers: List[TokenTransfer] = Field(default_factory=list)
    transaction_error: Optional[object] = None


class SignatureInfo(_BaseModel):
    signature: Optional[str] = None
    slot: Optional[int] = None
    block_time: Optional[int] = None
    confirmation_status: Optional[str] = None
    err: Optional[object] = None


class InstructionSummary(_BaseModel):
    program_ids: List[str] = Field(default_factory=list)


class TxRawSummary(_BaseModel):
    signature: Optional[str] = None
    slot: Optional[int] = None
    block_time: Optional[int] = None
    fee_lamports: Optional[int] = None
    err: Optional[object] = None
    program_ids: List[str] = Field(default_factory=list)
    log_messages: List[str] = Field(default_factory=list)


class SimulationSummary(_BaseModel):
    err: Optional[object] = None
    units_consumed: Optional[int] = None
    logs: List[str] = Field(default_factory=list)


class PriorityFeeLevels(_BaseModel):
    min: Optional[int] = None
    low: Optional[int] = None
    medium: Optional[int] = None
    high: Optional[int] = None
    veryHigh: Optional[int] = None
    unsafeMax: Optional[int] = None


class PriorityFeeSummary(_BaseModel):
    estimated_micro_lamports: int
    levels: Optional[PriorityFeeLevels] = None


class AssetSummary(_BaseModel):
    id: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    image: Optional[str] = None
    owner: Optional[str] = None
    collection: Optional[str] = None
    compressed: Optional[bool] = None
    interface: Optional[str] = None
    decimals: Optional[int] = None
    token_program: Optional[str] = None
    token_price_usd: Optional[float] = None



class AssetsPageSummary(_BaseModel):
    total: Optional[int] = None
    items: List[AssetSummary] = Field(default_factory=list)
    native_balance_lamports: Optional[int] = None


class TokenAccountSummary(_BaseModel):
    token_account: Optional[str] = None
    owner: Optional[str] = None
    mint: Optional[str] = None
    amount: Optional[str] = None
    decimals: Optional[int] = None
    ui_amount_string: Optional[str] = None

class TokenLargestAccountItem(_BaseModel):
    address: Optional[str] = None
    amount: Optional[str] = None
    decimals: Optional[int] = None
    ui_amount_string: Optional[str] = None


class TokenAccountsResult(_BaseModel):
    total: Optional[int] = None
    token_accounts: List[TokenAccountSummary] = Field(default_factory=list)


class AccountInfoSummary(_BaseModel):
    lamports: int
    owner: str
    executable: bool
    rent_epoch: int
    space: Optional[int] = None


class SignatureStatus(_BaseModel):
    slot: Optional[int] = None
    confirmations: Optional[int] = None
    err: Optional[object] = None
    status: Optional[Union[Dict[str, Any], str]] = None
    confirmation_status: Optional[str] = None


class ProgramAccountSummary(_BaseModel):
    pubkey: str
    account: AccountInfoSummary



# =============================
# RAW Schemas (direct API output)
# =============================

class RawEnhancedNativeTransfer(_BaseModel):
    from_user_account: Optional[str] = Field(default=None, alias="fromUserAccount")
    from_: Optional[str] = Field(default=None, alias="from")
    to_user_account: Optional[str] = Field(default=None, alias="toUserAccount")
    to_: Optional[str] = Field(default=None, alias="to")
    amount: Optional[int] = None


class RawEnhancedTokenTransfer(_BaseModel):
    mint: Optional[str] = None
    from_user_account: Optional[str] = Field(default=None, alias="fromUserAccount")
    from_token_account: Optional[str] = Field(default=None, alias="fromTokenAccount")
    from_: Optional[str] = Field(default=None, alias="from")
    to_user_account: Optional[str] = Field(default=None, alias="toUserAccount")
    to_token_account: Optional[str] = Field(default=None, alias="toTokenAccount")
    to_: Optional[str] = Field(default=None, alias="to")
    token_amount: Optional[Union[str, int, float, Dict[str, Any]]] = Field(default=None, alias="tokenAmount")
    decimals: Optional[int] = None

#TODO Build out
class RawEnhancedEvents(_BaseModel):
    events: Optional[List[Dict[str, Any]]] = None


class RawEnhancedTransaction(_BaseModel):
    # Top-level metadata
    description: Optional[str] = None
    type: Optional[str] = None
    source: Optional[str] = None
    fee: Optional[int] = None
    feePayer: Optional[str] = None
    signature: Optional[str] = None
    slot: Optional[int] = None
    timestamp: Optional[int] = None

    # Transfer summaries
    native_transfers: List[RawEnhancedNativeTransfer] = Field(default_factory=list, alias="nativeTransfers")
    token_transfers: List[RawEnhancedTokenTransfer] = Field(default_factory=list, alias="tokenTransfers")
    events: Optional[RawEnhancedEvents] = None

    # Status indicators (observed variants)
    status: Optional[Union[str, Dict[str, Any]]] = None
    transaction_error: Optional[Union[str, Dict[str, Any]]] = Field(default=None, alias="transactionError")    

    # Additional enhanced fields we don't currently consume, but preserve    
    accountData: Optional[List[Dict[str, Any]]] = None # Includes tokenBalanceChanges, nativeBalanceChange, and account.
    instructions: Optional[List[Dict[str, Any]]] = None

class RawSignatureForAddressItem(_BaseModel):
    signature: Optional[str] = None
    slot: Optional[int] = None
    err: Optional[object] = None
    memo: Optional[str] = None
    blockTime: Optional[int] = None
    confirmationStatus: Optional[str] = None

class RawInstruction(_BaseModel):
    accounts: Optional[List[str]] = Field(default_factory=list)
    data: Optional[str] = None
    programIdIndex: Optional[int] = None

class RawTransactionMessageHeader(_BaseModel):
    numReadonlySignedAccounts: Optional[int] = None
    numReadonlyUnsignedAccounts: Optional[int] = None
    numRequiredSignatures: Optional[int] = None

class RawTransactionMessageAccountKeys(_BaseModel):
    pubkey: Optional[str] = None
    writable: Optional[bool] = None

class RawTransactionMessage(_BaseModel):
    accountKeys: Optional[List[RawTransactionMessageAccountKeys]] = Field(default_factory=RawTransactionMessageAccountKeys)
    header: Optional[RawTransactionMessageHeader] = Field(default_factory=RawTransactionMessageHeader)
    recentBlockhash: Optional[str] = None
    instructions: Optional[List[RawInstruction]] = Field(default_factory=list)


class RawTransactionData(_BaseModel):
    message: RawTransactionMessage = Field(default_factory=RawTransactionMessage)
    signatures: List[str] = Field(default_factory=list)


class RawTransactionMeta(_BaseModel):
    err: Optional[object] = None
    fee: Optional[int] = None
    innerInstructions: Optional[List[Dict[str, Any]]] = None
    logMessages: Optional[List[str]] = None


class RawGetTransaction(_BaseModel):
    blockTime: Optional[int] = None
    slot: Optional[int] = None
    meta: Optional[RawTransactionMeta] = None
    transaction: Optional[RawTransactionData] = None

class RawContext(_BaseModel):
    apiVersion: Optional[str] = None
    slot: Optional[int] = None    


class RawReplacementBlockhash(_BaseModel):
    blockhash: Optional[str] = None
    lastValidBlockHeight: Optional[int] = None

class RawReturnData(_BaseModel):
    programId: Optional[str] = None
    data: Optional[str] = None


class RawSimulateTransactionValue(_BaseModel):
    accounts: Optional[List[Dict[str, Any]]] = None
    err: Optional[object] = None
    innerInstructions: Optional[List[Any]] = None
    loadedAccountsDataSize: Optional[int] = None
    logs: Optional[List[str]] = None
    replacementBlockhash: Optional[RawReplacementBlockhash] = None
    returnData: Optional[RawReturnData] = None
    unitsConsumed: Optional[int] = None


class RawSimulateTransactionResponse(_BaseModel):
    # Standard JSON-RPC response wraps it, but client returns .result directly
    context: Optional[RawContext] = None
    value: Optional[RawSimulateTransactionValue] = None    


class RawPriorityFeeLevels(_BaseModel):
    min: Optional[int] = None
    low: Optional[int] = None
    medium: Optional[int] = None
    high: Optional[int] = None
    veryHigh: Optional[int] = None
    unsafeMax: Optional[int] = None


class RawPriorityFeeEstimate(_BaseModel):
    priorityFeeEstimate: Optional[int] = None
    priorityFeeLevels: Optional[RawPriorityFeeLevels] = None


# --- DAS RAW ---------------------------------------------------------------

class RawDasAssetContentFile(_BaseModel):
    uri: Optional[str] = None
    cdn_uri: Optional[str] = None
    mime: Optional[str] = None


class RawDasAssetContentLinks(_BaseModel):
    image: Optional[str] = None
    external_url: Optional[str] = None


class RawDasAssetContentAttributes(_BaseModel):
    trait_type: Optional[str] = None
    value: Optional[str] = None


class RawDasAssetContentMetadata(_BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    attributes: Optional[List[RawDasAssetContentAttributes]] = None
    description: Optional[str] = None
    token_standard: Optional[str] = None


class RawDasAssetContent(_BaseModel):
    #$schema: Optional[str] = None
    json_uri: Optional[str] = None
    files: List[Union[RawDasAssetContentFile, Dict[str, Any]]] = Field(default_factory=list)
    links: Optional[RawDasAssetContentLinks] = None
    metadata: Optional[RawDasAssetContentMetadata] = None
    category: Optional[str] = None


class RawDasOwnership(_BaseModel):
    frozen: Optional[bool] = None
    delegated: Optional[bool] = None
    ownership_model: Optional[str] = None
    owner: Optional[str] = None
    delegate: Optional[str] = None


class RawDasGroupingItem(_BaseModel):
    group_key: Optional[str] = None
    group_value: Optional[str] = None


class RawDasCompression(_BaseModel):
    eligible: Optional[bool] = None
    compressed: Optional[bool] = None
    data_hash: Optional[str] = None
    creator_hash: Optional[str] = None
    asset_hash: Optional[str] = None
    tree: Optional[str] = None
    seq: Optional[int] = None
    leaf_id: Optional[int] = None


class RawTokenPriceInfo(_BaseModel):
    price_per_token: Optional[float] = None
    currency: Optional[str] = None


class RawDasTokenInfo(_BaseModel):
    symbol: Optional[str] = None
    supply: Optional[int] = None
    decimals: Optional[int] = None
    token_program: Optional[str] = None
    price_info: Optional[RawTokenPriceInfo] = None


class RawDasAuthorities(_BaseModel):
    address: Optional[str] = None
    scopes: Optional[List[str]] = None

class RawDasRoyalty(_BaseModel):
    royalty_model: Optional[str] = None
    target: Optional[str] = None
    percent: Optional[float] = None
    basis_points: Optional[int] = None
    primary_sale_happened: Optional[bool] = None
    locked: Optional[bool] = None

class RawDasCreator(_BaseModel):
    address: Optional[str] = None
    verified: Optional[bool] = None
    share: Optional[int] = None

class RawDasSupply(_BaseModel):
    print_max_supply: Optional[int] = None
    print_current_supply: Optional[int] = None
    edition_nonce: Optional[int] = None

class RawDasAsset(_BaseModel):
    id: str
    last_indexed_slot: Optional[int] = None
    interface: Optional[str] = None
    content: Optional[RawDasAssetContent] = None
    authorities: Optional[List[RawDasAuthorities]] = None
    compression: Optional[RawDasCompression] = None
    grouping: List[RawDasGroupingItem] = Field(default_factory=list)    
    royalty: Optional[RawDasRoyalty] = None
    creators: Optional[List[RawDasCreator]] = None
    ownership: Optional[RawDasOwnership] = None
    supply: Optional[RawDasSupply] = None
    mutable: Optional[bool] = None
    burnt: Optional[bool] = None
    token_info: Optional[RawDasTokenInfo] = None


class RawDasAssetsPage(_BaseModel):
    last_indexed_slot: Optional[int] = None
    page: Optional[int] = None
    total: Optional[int] = None
    items: Optional[List[RawDasAsset]] = Field(default_factory=list)
    limit: Optional[int] = None
    # Some responses include nativeBalance which may be an int or an object
    nativeBalance: Optional[Any] = None
    native_balance: Optional[Any] = None


class RawDasTokenAccountItem(_BaseModel):
    address: Optional[str] = None
    mint: Optional[str] = None
    owner: Optional[str] = None
    amount: Optional[int] = None
    delegated_amount: Optional[int] = None
    frozen: Optional[bool] = None
    #burnt: Optional[Any] = None
    #balance: Optional[RawDasTokenBalance] = None


class RawDasTokenBalance(_BaseModel):
    amount: Optional[Union[int, str]] = None
    decimals: Optional[int] = None
    uiAmountString: Optional[str] = None


class RawDasTokenAccountsResult(_BaseModel):
    last_indexed_slot: Optional[int] = None
    total: Optional[int] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None
    token_accounts: List[Union[RawDasTokenAccountItem, Dict[str, Any]]] = Field(default_factory=list)


# --- Helpers RAW -----------------------------------------------------------


class RawGetBalanceResult(_BaseModel):
    context: Optional[RawContext] = None
    value: int


class RawAccountInfoValue(_BaseModel):
    lamports: Optional[int] = None
    owner: Optional[str] = None
    data: Optional[Any] = None  # Can be List[str] or complex object depending on encoding
    executable: Optional[bool] = None
    rentEpoch: Optional[int] = None
    space: Optional[int] = None

class RawAccountStaticValue(_BaseModel):
    status: Optional[str] = None # "unchanged", Status-only response when account exists but hasn't changed since the specified slot.


class RawGetAccountInfoResult(_BaseModel):
    context: Optional[RawContext] = None
    value: Optional[RawAccountInfoValue | RawAccountStaticValue] = None


# --- Signature Statuses RAW --------------------------------------------------


class RawSignatureStatus(_BaseModel):
    slot: Optional[int] = None
    confirmations: Optional[int] = None
    err: Optional[object] = None
    confirmationStatus: Optional[str] = None
    status: Optional[Union[Dict[str, Any], str]] = None


class RawGetSignatureStatusesResult(_BaseModel):
    context: Optional[RawContext] = None
    value: Optional[List[Optional[RawSignatureStatus]]] = None


# --- Multiple Accounts RAW ---------------------------------------------------


class RawGetMultipleAccountsResult(_BaseModel):
    context: Optional[RawContext] = None
    value: Optional[List[Optional[RawAccountInfoValue | RawAccountStaticValue]]] = None


# --- Program Accounts RAW ----------------------------------------------------


class RawProgramAccount(_BaseModel):
    pubkey: str
    account: RawAccountInfoValue


# --- Token Largest Accounts --------------------------------------------------

class RawTokenLargestAccountItem(_BaseModel):
    address: Optional[str] = None
    amount: Optional[str] = None
    decimals: Optional[int] = None
    uiAmountString: Optional[str] = None


class RawTokenLargestAccounts(_BaseModel):
    context: Optional[RawContext] = None
    value: Optional[List[RawTokenLargestAccountItem]] = None

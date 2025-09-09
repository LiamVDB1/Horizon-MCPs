from __future__ import annotations

from typing import List, Optional

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
    compute_units_consumed: Optional[int] = None
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
    micro_lamports: int
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


class TokenAccountsResult(_BaseModel):
    total: Optional[int] = None
    items: List[TokenAccountSummary] = Field(default_factory=list)


class AccountInfoSummary(_BaseModel):
    lamports: int
    owner: str
    executable: bool
    rent_epoch: int
    space: Optional[int] = None



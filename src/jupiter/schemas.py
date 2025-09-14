from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Swap API ---


class AccountMeta(BaseModel):
    pubkey: str
    isSigner: bool
    isWritable: bool


class Instruction(BaseModel):
    programId: str
    accounts: List[AccountMeta]
    data: str


class SwapInfo(BaseModel):
    ammKey: str
    inputMint: str
    outputMint: str
    inAmount: str
    outAmount: str
    feeAmount: str
    feeMint: str
    label: Optional[str] = None


class RoutePlanStep(BaseModel):
    swapInfo: SwapInfo
    percent: int
    bps: Optional[int] = None


class PlatformFee(BaseModel):
    amount: Optional[str] = None
    feeBps: Optional[int] = None


class QuoteResponse(BaseModel):
    inputMint: str
    inAmount: str
    outputMint: str
    outAmount: str
    otherAmountThreshold: str
    swapMode: str
    slippageBps: int
    priceImpactPct: str
    routePlan: List[RoutePlanStep]
    platformFee: Optional[PlatformFee] = None
    contextSlot: Optional[int] = None
    timeTaken: Optional[float] = None


class SwapRequest(BaseModel):
    userPublicKey: str
    quoteResponse: QuoteResponse
    payer: Optional[str] = None
    wrapAndUnwrapSol: Optional[bool] = True
    useSharedAccounts: Optional[bool] = None
    feeAccount: Optional[str] = None
    trackingAccount: Optional[str] = None
    prioritizationFeeLamports: Optional[Dict[str, Any]] = None
    asLegacyTransaction: Optional[bool] = False
    destinationTokenAccount: Optional[str] = None
    dynamicComputeUnitLimit: Optional[bool] = False
    skipUserAccountsRpcCalls: Optional[bool] = False
    dynamicSlippage: Optional[bool] = False
    computeUnitPriceMicroLamports: Optional[int] = None
    blockhashSlotsToExpiry: Optional[int] = None


class SwapResponse(BaseModel):
    swapTransaction: str
    lastValidBlockHeight: int
    prioritizationFeeLamports: Optional[int] = None


class SwapInstructionsResponse(BaseModel):
    computeBudgetInstructions: List[Instruction]
    setupInstructions: List[Instruction]
    swapInstruction: Instruction
    cleanupInstruction: Optional[Instruction] = None
    addressLookupTableAddresses: List[str]
    otherInstructions: Optional[List[Instruction]] = None


# --- Ultra API ---


class TokenAccount(BaseModel):
    account: str
    amount: str
    uiAmount: float
    uiAmountString: str
    isFrozen: bool
    isAssociatedTokenAccount: bool
    decimals: int
    programId: str


class HoldingsResponse(BaseModel):
    amount: str
    uiAmount: float
    uiAmountString: str
    tokens: Dict[str, List[TokenAccount]]


class NativeHoldingsResponse(BaseModel):
    amount: str
    uiAmount: float
    uiAmountString: str


class ShieldWarning(BaseModel):
    type: str
    message: str
    severity: str
    source: Optional[str] = None


class UltraOrderResponse(BaseModel):
    mode: str
    inputMint: str
    outputMint: str
    inAmount: str
    outAmount: str
    otherAmountThreshold: str
    swapMode: str
    slippageBps: int
    routePlan: List[RoutePlanStep]
    feeBps: int
    signatureFeeLamports: int
    prioritizationFeeLamports: int
    rentFeeLamports: int
    router: str
    transaction: Optional[str]
    gasless: bool
    requestId: str
    totalTime: float
    taker: Optional[str]
    priceImpactPct: Optional[str] = None
    platformFee: Optional[PlatformFee] = None
    errorCode: Optional[int] = None
    errorMessage: Optional[str] = None


# --- Trigger API ---


class TriggerCreateParams(BaseModel):
    makingAmount: str
    takingAmount: str
    expiredAt: Optional[str] = None
    slippageBps: Optional[str] = Field(default="0")
    feeBps: Optional[str] = None


class TriggerCreateRequest(BaseModel):
    inputMint: str
    outputMint: str
    maker: str
    payer: str
    params: TriggerCreateParams
    computeUnitPrice: Optional[str] = Field(default="auto")
    feeAccount: Optional[str] = None
    wrapAndUnwrapSol: Optional[bool] = True


class TriggerTransactionResponse(BaseModel):
    requestId: str
    transaction: str
    order: Optional[str] = None


class TriggerCancelRequest(BaseModel):
    maker: str
    order: str
    computeUnitPrice: Optional[str] = Field(default="auto")


class TriggerCancelManyRequest(BaseModel):
    maker: str
    orders: Optional[List[str]] = None
    computeUnitPrice: Optional[str] = Field(default="auto")


# --- Recurring API (time-based) ---


class TimeRecurringCreationParams(BaseModel):
    inAmount: int
    numberOfOrders: int
    interval: int
    maxPrice: Optional[float] = None
    minPrice: Optional[float] = None
    startAt: Optional[int] = None


class RecurringCreateParams(BaseModel):
    time: TimeRecurringCreationParams


class RecurringCreateRequest(BaseModel):
    user: str
    inputMint: str
    outputMint: str
    params: RecurringCreateParams


class RecurringCloseType(BaseModel):
    # Use string union at call-site; keep model minimal
    pass


class RecurringCloseRequest(BaseModel):
    user: str
    order: str
    recurringType: str


class RecurringResponse(BaseModel):
    requestId: str
    transaction: str


# --- Token API v2 ---


class SwapStats(BaseModel):
    priceChange: Optional[float] = None
    holderChange: Optional[float] = None
    liquidityChange: Optional[float] = None
    volumeChange: Optional[float] = None
    buyVolume: Optional[float] = None
    sellVolume: Optional[float] = None
    buyOrganicVolume: Optional[float] = None
    sellOrganicVolume: Optional[float] = None
    numBuys: Optional[float] = None
    numSells: Optional[float] = None
    numTraders: Optional[float] = None
    numOrganicBuyers: Optional[float] = None
    numNetBuyers: Optional[float] = None


class MintInformation(BaseModel):
    id: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    icon: Optional[str] = None
    decimals: Optional[float] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    website: Optional[str] = None
    dev: Optional[str] = None
    circSupply: Optional[float] = None
    totalSupply: Optional[float] = None
    tokenProgram: Optional[str] = None
    launchpad: Optional[str] = None
    partnerConfig: Optional[str] = None
    graduatedPool: Optional[str] = None
    graduatedAt: Optional[str] = None
    holderCount: Optional[float] = None
    fdv: Optional[float] = None
    mcap: Optional[float] = None
    usdPrice: Optional[float] = None
    priceBlockId: Optional[float] = None
    liquidity: Optional[float] = None
    stats5m: Optional[SwapStats] = None
    stats1h: Optional[SwapStats] = None
    stats6h: Optional[SwapStats] = None
    stats24h: Optional[SwapStats] = None
    organicScore: Optional[float] = None
    organicScoreLabel: Optional[str] = None
    isVerified: Optional[bool] = None
    cexes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    updatedAt: Optional[str] = None


# --- Price API v3 ---


class PriceItem(BaseModel):
    decimals: int
    usdPrice: float
    blockId: Optional[int] = None
    priceChange24h: Optional[float] = None


# --- Lend / Earn ---


class AccountMetaLend(BaseModel):
    pubkey: str
    isSigner: bool
    isWritable: bool


class InstructionResponse(BaseModel):
    programId: str
    accounts: List[AccountMetaLend]
    data: str


class TransactionResponse(BaseModel):
    transaction: str


class EarnAmountRequest(BaseModel):
    asset: str
    signer: str
    amount: str


class EarnSharesRequest(BaseModel):
    asset: str
    signer: str
    shares: str


class AssetInfo(BaseModel):
    address: str
    chain_id: str
    name: str
    symbol: str
    decimals: int
    logo_url: str
    price: str
    coingecko_id: str


class LiquiditySupplyData(BaseModel):
    modeWithInterest: bool
    supply: str
    withdrawalLimit: str
    lastUpdateTimestamp: str
    expandPercent: str
    expandDuration: str
    baseWithdrawalLimit: str
    withdrawableUntilLimit: str
    withdrawable: str


class TokenInfo(BaseModel):
    id: int
    address: str
    name: str
    symbol: str
    decimals: int
    assetAddress: str
    asset: AssetInfo
    totalAssets: str
    totalSupply: str
    convertToShares: str
    convertToAssets: str
    rewardsRate: str
    supplyRate: str
    totalRate: str
    rebalanceDifference: str
    liquiditySupplyData: LiquiditySupplyData


class UserPosition(BaseModel):
    token: TokenInfo
    ownerAddress: str
    shares: str
    underlyingAssets: str
    underlyingBalance: str
    allowance: str


# --- Send API ---


class CraftSendRequest(BaseModel):
    inviteSigner: str
    sender: str
    amount: str
    mint: Optional[str] = None


class CraftSendResponse(BaseModel):
    tx: str
    expiry: str
    totalFeeLamports: str


class CraftClawbackRequest(BaseModel):
    invitePDA: str
    sender: str


class CraftClawbackResponse(BaseModel):
    tx: str


# --- Studio (DBC) ---


class CreateDBCTransactionRequestBody(BaseModel):
    buildCurveByMarketCapParam: Dict[str, Any]
    antiSniping: bool
    fee: Dict[str, Any]
    tokenName: str
    tokenSymbol: str
    tokenImageContentType: str
    creator: str
    isLpLocked: Optional[bool] = True


class CreateDBCTransactionResponse(BaseModel):
    transaction: str
    mint: str
    imagePresignedUrl: str
    metadataPresignedUrl: str
    imageUrl: str


class CreateClaimFeeDBCTransactionRequestBody(BaseModel):
    ownerWallet: str
    poolAddress: str
    maxQuoteAmount: float



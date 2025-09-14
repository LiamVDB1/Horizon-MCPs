"""
Helius FastMCP server for Solana.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from fastmcp import FastMCP

from src.helius.services import HeliusService


mcp = FastMCP(
    "helius-mcp",
    "Helius-based Solana helper. Enhanced-first; RPC+DAS for completeness.",
)


_service = HeliusService()


def _as_dict(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_as_dict(x) for x in obj]
    return obj


# --- Enhanced (REST) -------------------------------------------------------


def get_transactions(signatures: List[str], network: str = "mainnet") -> List[Dict[str, Any]]:
    """Decode tx signatures via Enhanced API (human-readable)."""
    return _as_dict(_service.get_transactions(signatures, network))


def get_transactions_by_address(
    address: str,
    network: str = "mainnet",
    tx_type: Optional[str] = None,
    source: Optional[str] = None,
    before: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 50,
    commitment: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Enhanced history for an address with filters."""
    return _as_dict(
        _service.get_transactions_by_address(address, network, tx_type, source, before, until, limit, commitment)
    )


# --- RPC (fallback, logs, completeness) ------------------------------------


def get_signatures_for_address(
    address: str,
    network: str = "mainnet",
    limit: int = 1000,
    before: Optional[str] = None,
    until: Optional[str] = None,
    commitment: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Confirmed signatures for an address."""
    return _as_dict(_service.get_signatures_for_address(address, network, limit, before, until, commitment))


def get_transaction_raw(
    signature: str,
    network: str = "mainnet",
    encoding: str = "jsonParsed",
    commitment: Optional[str] = None,
) -> Dict[str, Any]:
    """Raw getTransaction when Enhanced lacks coverage."""
    return _as_dict(_service.get_transaction_raw(signature, network, encoding, commitment))


def simulate_transaction(
    transaction: str,
    network: str = "mainnet",
    sig_verify: bool = False,
    commitment: Optional[str] = None,
) -> Dict[str, Any]:
    """Simulate a serialized tx (logs, CU, balances)."""
    return _as_dict(_service.simulate_transaction(transaction, network, sig_verify, commitment))


def get_priority_fee_estimate(
    network: str = "mainnet",
    transaction: Optional[str] = None,
    account_keys: Optional[List[str]] = None,
    priority_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Priority fee estimate. Provide transaction or account_keys."""
    return _as_dict(_service.get_priority_fee_estimate(network, transaction, account_keys, priority_level))

def get_signature_statuses(
    signatures: List[str],
    network: str = "mainnet",
    search_transaction_history: bool = False,
    commitment: Optional[str] = None,
) -> List[Optional[Dict[str, Any]]]:
    """Statuses for multiple signatures (processed/confirmed/finalized)."""
    return _as_dict(
        _service.get_signature_statuses(signatures, network, search_transaction_history, commitment)
    )


def get_multiple_accounts(
    pubkeys: List[str],
    network: str = "mainnet",
    encoding: str = "jsonParsed",
    commitment: Optional[str] = None,
    data_slice: Optional[Dict[str, int]] = None,
    min_context_slot: Optional[int] = None,
    changed_since_slot: Optional[int] = None,
) -> List[Optional[Dict[str, Any]]]:
    """Batch account info for many pubkeys."""
    return _as_dict(
        _service.get_multiple_accounts(
            pubkeys,
            network,
            encoding,
            commitment,
            data_slice,
            min_context_slot,
            changed_since_slot,
        )
    )


def get_program_accounts(
    program_id: str,
    network: str = "mainnet",
    encoding: str = "base64",
    filters: Optional[List[Dict[str, Any]]] = None,
    data_slice: Optional[Dict[str, int]] = None,
    commitment: Optional[str] = None,
    changed_since_slot: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Accounts owned by a program with optional filters."""
    return _as_dict(
        _service.get_program_accounts(
            program_id,
            network,
            encoding,
            filters,
            data_slice,
            commitment,
            changed_since_slot,
        )
    )


def get_token_largest_accounts(
    mint: str,
    network: str = "mainnet",
    commitment: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Top 20 largest accounts for a token mint."""
    return _as_dict(_service.get_token_largest_accounts(mint, network, commitment))


# --- DAS (assets & portfolios) ---------------------------------------------


def get_asset(asset_id: str, network: str = "mainnet") -> Dict[str, Any]:
    """Full metadata for one asset (NFT/cNFT/token)."""
    return _as_dict(_service.get_asset(asset_id, network))


def get_assets_by_owner(
    owner_address: str,
    page: int = 1,
    limit: int = 50,
    network: str = "mainnet",
    show_fungible: bool = False,
    show_native_balance: bool = False,
    show_zero_balance: bool = False,
) -> Dict[str, Any]:
    """Portfolio: NFTs, compressed, fungibles, optional SOL."""
    return _as_dict(
        _service.get_assets_by_owner(owner_address, page, limit, network, show_fungible, show_native_balance, show_zero_balance)
    )


def search_assets(
    network: str = "mainnet",
    owner_address: Optional[str] = None,
    token_type: str = "all",
    creator_address: Optional[str] = None,
    collection: Optional[str] = None,
    attributes: Optional[Dict[str, str]] = None,
    limit: int = 50,
    page: int = 1,
) -> Dict[str, Any]:
    """Search assets by owner/creator/collection/attributes."""
    return _as_dict(
        _service.search_assets(network, owner_address, token_type, creator_address, collection, attributes, limit, page)
    )


def get_token_accounts(
    owner: str,
    mint: Optional[str] = None,
    network: str = "mainnet",
) -> Dict[str, Any]:
    """Token accounts and balances for an owner."""
    return _as_dict(_service.get_token_accounts(owner, mint, network))


# --- Small helpers ----------------------------------------------------------


def get_balance(
    public_key: str,
    network: str = "mainnet",
    commitment: Optional[str] = None,
) -> int:
    """Lamport balance for an address."""
    return _service.get_balance(public_key, network, commitment)


def get_account_info(
    address: str,
    network: str = "mainnet",
    encoding: str = "base64",
) -> Dict[str, Any]:
    """Account data and owner."""
    return _as_dict(_service.get_account_info(address, network, encoding))


def register_mcp_prompts_and_resources() -> None:
    """Optional registration hooks for MCP prompts/resources."""
    try:
        # Example prompt placeholder (customize as needed)
        if hasattr(mcp, "add_prompt"):
            mcp.add_prompt(
                name="helius_summary",
                description="Summarize a Solana transaction by signature",
                message="Given signature: {{signature}}",
                variables=[{"name": "signature", "description": "Transaction signature"}],
            )  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        # Example resource placeholder (customize as needed)
        if hasattr(mcp, "add_resource"):
            mcp.add_resource(
                uri="resource://helius/docs",
                mimeType="text/markdown",
                name="Helius MCP Docs",
                description="Usage examples and tips",
                text="# Helius MCP Resources\n\nSee tools for details.",
            )  # type: ignore[attr-defined]
    except Exception:
        pass


def register_mcp_tools() -> None:
    # Register tools programmatically to keep functions callable for tests
    mcp.tool()(get_transactions)
    mcp.tool()(get_transactions_by_address)
    mcp.tool()(get_signatures_for_address)
    mcp.tool()(get_transaction_raw)
    mcp.tool()(simulate_transaction)
    mcp.tool()(get_priority_fee_estimate)
    mcp.tool()(get_signature_statuses)
    mcp.tool()(get_multiple_accounts)
    mcp.tool()(get_program_accounts)
    mcp.tool()(get_token_largest_accounts)
    mcp.tool()(get_asset)
    mcp.tool()(get_assets_by_owner)
    mcp.tool()(search_assets)
    mcp.tool()(get_token_accounts)
    mcp.tool()(get_balance)
    mcp.tool()(get_account_info)


if __name__ == "__main__":
    register_mcp_prompts_and_resources()
    register_mcp_tools()
    mcp.run(transport="streamable-http", host="127.0.0.1", port=9120, path="/mcp")



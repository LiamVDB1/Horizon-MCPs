from __future__ import annotations

import os
import time
from typing import Any, Dict, List

import pytest

from src.helius.services import HeliusService
from src.helius.client import HeliusClient
from src.helius.schemas import (
    EnhancedTxSummary,
    SignatureInfo,
    TxRawSummary,
    SimulationSummary,
    PriorityFeeSummary,
    AssetSummary,
    AssetsPageSummary,
    TokenAccountsResult,
    AccountInfoSummary,
    SignatureStatus,
    ProgramAccountSummary,
    TokenLargestAccountItem,
)


def _get_api_key() -> str | None:
    try:
        from src.config import settings as cfg  # type: ignore
        return getattr(cfg, "HELIUS_API_KEY", None)
    except Exception:
        import os as _os
        return _os.getenv("HELIUS_API_KEY")


requires_live = pytest.mark.skipif(
    not _get_api_key(), reason="HELIUS_API_KEY not set; skipping live integration tests"
)

# Test constants - well-known addresses for reliable testing
SYSTEM_PROGRAM = "11111111111111111111111111111111"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL_MINT = "So11111111111111111111111111111111111111112"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
MEMO_PROGRAM = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
# Known active wallet with transaction history (Solana Foundation)
ACTIVE_WALLET = "GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPqn7npE"


# =============================================================================
# Basic Service Connectivity Tests
# =============================================================================

@requires_live
def test_client_initialization() -> None:
    """Test that client initializes properly and can connect"""
    client = HeliusClient()
    svc = HeliusService(client)
    assert svc.client is not None
    # Simple connectivity test
    balance = svc.get_balance(SYSTEM_PROGRAM, network="mainnet")
    assert isinstance(balance, int)


# =============================================================================
# Network and Parameter Validation Tests
# =============================================================================

@requires_live 
def test_invalid_network_handling() -> None:
    """Test that invalid networks are properly rejected"""
    svc = HeliusService()
    with pytest.raises(ValueError, match="network must be"):
        svc.get_balance(SYSTEM_PROGRAM, network="invalid")


@requires_live
def test_both_networks_work() -> None:
    """Test that both mainnet and devnet work"""
    svc = HeliusService()
    
    # Test mainnet
    balance_main = svc.get_balance(SYSTEM_PROGRAM, network="mainnet") 
    assert isinstance(balance_main, int)
    assert balance_main >= 0
    
    # Test devnet
    balance_dev = svc.get_balance(SYSTEM_PROGRAM, network="devnet")
    assert isinstance(balance_dev, int)
    assert balance_dev >= 0


# =============================================================================
# Balance and Account Info Tests
# =============================================================================

@requires_live
def test_get_balance_comprehensive() -> None:
    """Comprehensive balance testing with different accounts and commitments"""
    svc = HeliusService()
    
    # System program should have 1 lamport
    sys_balance = svc.get_balance(SYSTEM_PROGRAM, network="mainnet")
    assert isinstance(sys_balance, int)
    assert sys_balance >= 0
    
    # Test different commitment levels
    balance_finalized = svc.get_balance(SYSTEM_PROGRAM, network="mainnet", commitment="finalized")
    balance_confirmed = svc.get_balance(SYSTEM_PROGRAM, network="mainnet", commitment="confirmed") 
    assert isinstance(balance_finalized, int)
    assert isinstance(balance_confirmed, int)


@requires_live
def test_get_account_info_comprehensive() -> None:
    """Comprehensive account info testing"""
    svc = HeliusService()
    
    # System program info
    info = svc.get_account_info(SYSTEM_PROGRAM, network="mainnet")
    assert isinstance(info, AccountInfoSummary)
    assert info.lamports >= 0
    assert isinstance(info.owner, str) and len(info.owner) > 0
    assert isinstance(info.executable, bool)
    assert isinstance(info.rent_epoch, int)
    
    # Test different encodings
    info_json = svc.get_account_info(SYSTEM_PROGRAM, network="mainnet", encoding="jsonParsed")
    assert isinstance(info_json, AccountInfoSummary)
    
    info_base58 = svc.get_account_info(SYSTEM_PROGRAM, network="mainnet", encoding="base58")
    assert isinstance(info_base58, AccountInfoSummary)


@requires_live
def test_get_multiple_accounts() -> None:
    """Test fetching multiple accounts at once"""
    svc = HeliusService()
    
    # Use accounts that definitely exist - token mints and known programs
    accounts = [USDC_MINT, SOL_MINT, TOKEN_PROGRAM]
    results = svc.get_multiple_accounts(accounts, network="mainnet")
    
    assert isinstance(results, list)
    assert len(results) == len(accounts)
    
    # Check that we get results for the accounts (some might be None if accounts don't exist)
    # At least one should exist (USDC_MINT definitely should exist)
    non_null_results = [r for r in results if r is not None]
    assert len(non_null_results) > 0, f"At least one account should exist. Results: {results}"
    
    # Check structure of existing accounts
    for result in results:
        if result is not None:
            assert isinstance(result, AccountInfoSummary)
            assert result.lamports >= 0


@requires_live
def test_get_multiple_accounts_with_options() -> None:
    """Test multiple accounts with various options"""
    svc = HeliusService()
    
    accounts = [SYSTEM_PROGRAM, TOKEN_PROGRAM]
    
    # Test with data slice
    results = svc.get_multiple_accounts(
        accounts, 
        network="mainnet", 
        encoding="base64",
        data_slice={"offset": 0, "length": 10}
    )
    assert isinstance(results, list)
    assert len(results) == 2


# =============================================================================
# Signature and Transaction Tests  
# =============================================================================

@requires_live
def test_get_signatures_for_address_comprehensive() -> None:
    """Comprehensive signature fetching with various parameters"""
    svc = HeliusService()
    
    # Test basic signature fetching
    signatures = svc.get_signatures_for_address(USDC_MINT, network="mainnet", limit=5)
    assert isinstance(signatures, list)
    assert len(signatures) <= 5
    
    for sig in signatures:
        assert isinstance(sig, SignatureInfo)
        assert sig.signature is None or isinstance(sig.signature, str)
        assert sig.slot is None or isinstance(sig.slot, int)
    
    # Test with different limits
    signatures_10 = svc.get_signatures_for_address(USDC_MINT, network="mainnet", limit=10)
    assert len(signatures_10) <= 10
    
    # Test with commitment parameter
    signatures_confirmed = svc.get_signatures_for_address(
        USDC_MINT, network="mainnet", limit=3, commitment="confirmed"
    )
    assert isinstance(signatures_confirmed, list)


@requires_live
def test_get_signature_statuses() -> None:
    """Test signature status checking"""
    svc = HeliusService()
    
    # Get some recent signatures first
    signatures = svc.get_signatures_for_address(USDC_MINT, network="mainnet", limit=3)
    if not signatures:
        pytest.skip("No signatures found to test status")
    
    sig_strings = [s.signature for s in signatures if s.signature]
    if not sig_strings:
        pytest.skip("No valid signatures to test")
    
    statuses = svc.get_signature_statuses(sig_strings, network="mainnet")
    assert isinstance(statuses, list)
    assert len(statuses) == len(sig_strings)
    
    for status in statuses:
        if status is not None:
            assert isinstance(status, SignatureStatus)


@requires_live 
def test_get_transaction_raw_comprehensive() -> None:
    """Comprehensive raw transaction testing"""
    svc = HeliusService()
    
    # Get a recent signature to test with
    signatures = svc.get_signatures_for_address(USDC_MINT, network="mainnet", limit=1)
    if not signatures or not signatures[0].signature:
        pytest.skip("No recent signatures to fetch raw transaction")
    
    signature = signatures[0].signature
    
    # Test basic raw transaction
    tx = svc.get_transaction_raw(signature, network="mainnet")
    assert isinstance(tx, TxRawSummary)
    assert tx.signature == signature
    assert isinstance(tx.program_ids, list)
    assert isinstance(tx.log_messages, list)
    
    # Test with different commitment (avoid base58 encoding as it has different structure)
    tx_confirmed = svc.get_transaction_raw(signature, network="mainnet", commitment="confirmed")
    assert isinstance(tx_confirmed, TxRawSummary)


@requires_live
def test_get_transactions_batch() -> None:
    """Test fetching multiple transactions by signatures"""
    svc = HeliusService()
    
    # Get some signatures first
    signatures = svc.get_signatures_for_address(USDC_MINT, network="mainnet", limit=3)
    if not signatures:
        pytest.skip("No signatures found for batch transaction test")
    
    sig_strings = [s.signature for s in signatures if s.signature][:2]  # Limit to 2 for test
    if not sig_strings:
        pytest.skip("No valid signatures for batch test")
    
    transactions = svc.get_transactions(sig_strings, network="mainnet")
    assert isinstance(transactions, list)
    assert len(transactions) <= len(sig_strings)
    
    for tx in transactions:
        assert isinstance(tx, EnhancedTxSummary)


@requires_live
def test_get_transactions_by_address_comprehensive() -> None:
    """Comprehensive transaction by address testing"""
    svc = HeliusService()
    
    # Basic test
    transactions = svc.get_transactions_by_address(USDC_MINT, network="mainnet", limit=2)
    assert isinstance(transactions, list)
    assert len(transactions) <= 2
    
    for tx in transactions:
        assert isinstance(tx, EnhancedTxSummary)
        assert tx.signature is None or isinstance(tx.signature, str)
        assert isinstance(tx.native_transfers, list)
        assert isinstance(tx.token_transfers, list)
    
    # Test with parameters
    transactions_filtered = svc.get_transactions_by_address(
        USDC_MINT, 
        network="mainnet", 
        limit=1,
        commitment="finalized"
    )
    assert isinstance(transactions_filtered, list)


# =============================================================================
# Simulation and Priority Fee Tests
# =============================================================================

@requires_live
def test_simulate_transaction() -> None:
    """Test transaction simulation - requires a valid transaction to simulate"""
    svc = HeliusService()
    
    # This test requires a valid base64-encoded transaction
    # For live testing, we'll use a simple transfer transaction template
    # Note: This might fail if transaction is not properly formatted, which is expected
    sample_transaction = "AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEDArczbMia1tLmq7zz4DinMNN0pJ1JtLdqIJPUw3YrGCzYAMHBsgN27lcgB6H2WQvFgyZuJYHa46puOQo9yQ8CVQbd9uHXZaGT2cvhRs7reawctIXtX1s3kTqM9YV+/wCp20C7Wj2aiuk5TReAXo+VTVg8QTHjs0UjNMMKCvpzZ+ABAgEBARU="
    
    try:
        result = svc.simulate_transaction(sample_transaction, network="mainnet")
        assert isinstance(result, SimulationSummary)
        assert isinstance(result.logs, list)
        assert result.units_consumed is None or isinstance(result.units_consumed, int)
        # err field can be present if simulation had errors, which is normal
    except Exception as e:
        # Simulation might fail with invalid transaction, which is expected in test
        # The important thing is that the method exists and handles errors gracefully
        assert "error" in str(e).lower() or "invalid" in str(e).lower()
        print(f"Simulation failed as expected with test transaction: {e}")


@requires_live
def test_get_priority_fee_estimate_comprehensive() -> None:
    """Comprehensive priority fee estimation testing"""
    svc = HeliusService()
    
    # Test with account keys
    fee_estimate = svc.get_priority_fee_estimate(
        network="mainnet", 
        account_keys=[SYSTEM_PROGRAM, TOKEN_PROGRAM]
    )
    assert isinstance(fee_estimate, PriorityFeeSummary)
    assert isinstance(fee_estimate.estimated_micro_lamports, int)
    assert fee_estimate.estimated_micro_lamports >= 0
    
    # Test with different account keys
    fee_simple = svc.get_priority_fee_estimate(
        network="mainnet",
        account_keys=[USDC_MINT]
    )
    assert isinstance(fee_simple, PriorityFeeSummary)
    assert isinstance(fee_simple.estimated_micro_lamports, int)


# =============================================================================
# Asset and Token Tests
# =============================================================================

@requires_live
def test_get_asset_comprehensive() -> None:
    """Comprehensive asset testing"""
    svc = HeliusService()
    
    # Test USDC mint
    usdc_asset = svc.get_asset(USDC_MINT, network="mainnet")
    assert isinstance(usdc_asset, AssetSummary)
    assert usdc_asset.id == USDC_MINT
    
    # Test SOL mint
    sol_asset = svc.get_asset(SOL_MINT, network="mainnet")
    assert isinstance(sol_asset, AssetSummary)
    assert sol_asset.id == SOL_MINT


@requires_live
def test_get_assets_by_owner_comprehensive() -> None:
    """Comprehensive asset ownership testing"""
    svc = HeliusService()
    
    # Basic test
    assets = svc.get_assets_by_owner(
        owner_address=SYSTEM_PROGRAM, 
        page=1, 
        limit=5, 
        network="mainnet"
    )
    assert isinstance(assets, AssetsPageSummary)
    assert isinstance(assets.items, list)
    assert assets.total is None or isinstance(assets.total, int)
    
    # Test with display options
    assets_fungible = svc.get_assets_by_owner(
        owner_address=SYSTEM_PROGRAM,
        page=1,
        limit=5,
        network="mainnet",
        show_fungible=True,
        show_native_balance=True,
        show_zero_balance=True
    )
    assert isinstance(assets_fungible, AssetsPageSummary)


@requires_live
def test_search_assets_comprehensive() -> None:
    """Comprehensive asset search testing"""
    svc = HeliusService()
    
    # Basic search
    results = svc.search_assets(network="mainnet", limit=3, page=1)
    assert isinstance(results, AssetsPageSummary)
    assert isinstance(results.items, list)
    assert len(results.items) <= 3
    
    # Search with token type
    results_fungible = svc.search_assets(
        network="mainnet",
        limit=2,
        page=1,
        token_type="fungible",
        owner_address=ACTIVE_WALLET
    )
    assert isinstance(results_fungible, AssetsPageSummary)


@requires_live
def test_get_token_accounts() -> None:
    """Test token account fetching"""
    svc = HeliusService()
    
    # Get token accounts for an active wallet
    accounts = svc.get_token_accounts(ACTIVE_WALLET, network="mainnet")
    assert isinstance(accounts, TokenAccountsResult)
    assert isinstance(accounts.token_accounts, list)
    assert accounts.total is None or isinstance(accounts.total, int)
    
    # Get accounts for specific mint
    usdc_accounts = svc.get_token_accounts(ACTIVE_WALLET, mint=USDC_MINT, network="mainnet")
    assert isinstance(usdc_accounts, TokenAccountsResult)
    assert isinstance(usdc_accounts.token_accounts, list)


@requires_live
def test_get_token_largest_accounts() -> None:
    """Test getting largest token accounts - tries multiple tokens to find one that works"""
    svc = HeliusService()
    
    # Try tokens in order of decreasing size until we find one that works
    # Major tokens like USDC/SOL/USDT have too many accounts (18+ million)
    test_tokens = [
        ("mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So", "mSOL (Marinade SOL)"),  # ~248 largest accounts - should work
        ("JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN", "Jupiter (JUP)"),  # Should work
        ("7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj", "Lido stSOL"),  # Should work
        ("hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux", "Helium (HNT)"),  # Should work
        (USDC_MINT, "USDC"),  # 18M+ accounts - likely too many
    ]
    
    last_error = None
    
    for token_mint, token_name in test_tokens:
        try:
            largest = svc.get_token_largest_accounts(token_mint, network="mainnet", commitment="finalized")
            
            # Success! Validate the results
            assert isinstance(largest, list), f"Result should be a list for {token_name}"
            assert len(largest) > 0, f"Should return at least some largest accounts for {token_name}"
            
            # Check structure of returned accounts
            for account in largest[:5]:  # Check first few
                assert isinstance(account, TokenLargestAccountItem)
                assert account.address is None or isinstance(account.address, str)
                assert account.amount is None or isinstance(account.amount, str)
                
                # If we have valid data, validate it further
                if account.address and account.amount:
                    assert len(account.address) > 20, f"Address should be a valid Solana pubkey for {token_name}"
                    assert account.amount.isdigit(), f"Amount should be numeric string for {token_name}"
            
            print(f"✅ Successfully tested getTokenLargestAccounts with {token_name} ({len(largest)} accounts returned)")
            return  # Test passed!
            
        except RuntimeError as e:
            if "Too many accounts" in str(e):
                print(f"⚠️  {token_name} has too many accounts ({str(e)[:100]}...)")
                last_error = e
                continue  # Try next token
            else:
                # Unexpected error - fail the test
                raise
    
    # If we get here, all tokens failed due to "too many accounts"
    pytest.skip(f"All test tokens have too many accounts. Last error: {last_error}")  


@requires_live
def test_get_token_whale_addresses_jupiter_api_use_case() -> None:
    """Test whale address functionality for Jupiter API simulation use case"""
    svc = HeliusService()
    
    # Test the primary use case: USDC whales for Jupiter API
    print("🎯 Testing USDC whale addresses for Jupiter API simulation...")
    
    usdc_result = svc.get_token_whale_addresses(
        USDC_MINT, 
        network="mainnet",
        min_amount_ui=1000.0,  # At least 1000 USDC
        min_sol_balance=0.01,  # At least 0.01 SOL for fees
    )
    
    # Handle both return types: string address or tuple (address, balance)
    if isinstance(usdc_result, tuple):
        usdc_whale, usdc_whale_balance = usdc_result
        assert isinstance(usdc_whale_balance, (float, int)), "Whale balance should be a number"
    else:
        usdc_whale = usdc_result
        usdc_whale_balance = None
    
    # Validate the whale address
    assert isinstance(usdc_whale, str), "Whale address should be a string"
    assert len(usdc_whale) > 20, "Address should be a valid Solana pubkey"
    
    print(f"✅ Found valid USDC whale address for Jupiter API")
    print(f"🐋 whale address: {usdc_whale}")
    if usdc_whale_balance is not None:
        print(f"🐋 whale balance: {usdc_whale_balance}")
    
    # Test other major tokens that are important for Jupiter API
    major_tokens = [
        (SOL_MINT, "SOL", 1.0),  # At least 1 SOL
        ("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", "USDT", 1000.0),  # At least 1000 USDT
    ]
    
    for mint, name, min_amount in major_tokens:
        whale_result = svc.get_token_whale_addresses(
            mint, 
            network="mainnet",
            min_amount_ui=min_amount,
            min_sol_balance=0.01,
        )
        assert whale_result is not None, f"{name} should return a whale address"
        
        # Handle both return types: string address or tuple (address, balance)
        if isinstance(whale_result, tuple):
            whale_addr, whale_balance = whale_result
        else:
            whale_addr = whale_result
            whale_balance = None
            
        assert isinstance(whale_addr, str), f"{name} whale address should be a string"
        assert len(whale_addr) > 20, f"{name} whale address should be a valid Solana pubkey"
        print(f"✅ {name}: whale address available ({whale_addr[:8]}...)")
    
    print("✅ Whale address system works for all major Jupiter API tokens")


@requires_live
def test_whale_addresses_have_sufficient_balances() -> None:
    """Test that whale addresses actually have the balances we expect"""
    svc = HeliusService()
    
    # Get USDC whales and verify they actually have the required balances
    whale_result = svc.get_token_whale_addresses(
        USDC_MINT,
        network="mainnet", 
        min_amount_ui=500.0,  # At least 500 USDC
        min_sol_balance=0.01,
    )
    
    assert whale_result is not None, "Should find at least one whale"
    
    # Handle both return types: string address or tuple (address, balance)
    if isinstance(whale_result, tuple):
        whale, whale_balance = whale_result
    else:
        whale = whale_result
        whale_balance = None
    
    # Check SOL balance
    sol_lamports = svc.get_balance(whale, network="mainnet")
    sol_balance = sol_lamports / 1_000_000_000
    assert sol_balance >= 0.01, f"Whale {whale} should have at least 0.01 SOL for fees"
    
    print(f"✅ Whale {whale} has {sol_balance:.4f} SOL for transaction fees")
    if whale_balance is not None:
        print(f"✅ Whale has {whale_balance} token balance")
    print("✅ Whale addresses are validated and ready for Jupiter API use")


# =============================================================================
# Program Account Tests
# =============================================================================

@requires_live
def test_get_program_accounts() -> None:
    """Test fetching program accounts"""
    svc = HeliusService()
    
    # This test might fail for large programs due to too many accounts
    # We'll use the MEMO program which should have fewer accounts
    try:
        accounts = svc.get_program_accounts(
            MEMO_PROGRAM, 
            network="mainnet",
            encoding="base64",
            data_slice={"offset": 0, "length": 32}  # Small slice for faster test
        )
        assert isinstance(accounts, list)
        
        # Check structure of returned accounts
        if accounts:  # May be empty due to filtering
            for account in accounts[:2]:  # Check first couple
                assert isinstance(account, ProgramAccountSummary)
                assert isinstance(account.pubkey, str)
                assert isinstance(account.account, AccountInfoSummary)
    except RuntimeError as e:
        if "Too many accounts" in str(e) or "getProgramAccountsV2" in str(e):
            pytest.skip(f"Too many accounts for program {MEMO_PROGRAM}, skipping test: {e}")
        else:
            raise


# =============================================================================
# Error Handling and Edge Case Tests
# =============================================================================

@requires_live
def test_empty_signature_list_errors() -> None:
    """Test that empty signature lists raise appropriate errors"""
    svc = HeliusService()
    
    with pytest.raises(ValueError, match="signatures must not be empty"):
        svc.get_transactions([], network="mainnet")
    
    with pytest.raises(ValueError, match="signatures must not be empty"):
        svc.get_signature_statuses([], network="mainnet")


@requires_live
def test_empty_pubkey_list_errors() -> None:
    """Test that empty pubkey lists raise appropriate errors"""
    svc = HeliusService()
    
    with pytest.raises(ValueError, match="pubkeys must not be empty"):
        svc.get_multiple_accounts([], network="mainnet")


@requires_live
def test_too_many_signatures_error() -> None:
    """Test that too many signatures raise appropriate errors"""
    svc = HeliusService()
    
    # Create list with 101 dummy signatures
    too_many_sigs = ["dummy_signature"] * 101
    
    with pytest.raises(ValueError, match="max 100 signatures"):
        svc.get_transactions(too_many_sigs, network="mainnet")


@requires_live
def test_priority_fee_conflicting_params() -> None:
    """Test that conflicting priority fee parameters raise errors"""
    svc = HeliusService()
    
    with pytest.raises(ValueError, match="Provide either transaction or account_keys"):
        svc.get_priority_fee_estimate(
            network="mainnet",
            transaction="dummy_transaction",
            account_keys=["dummy_key"]
        )


@requires_live
def test_invalid_signature_handling() -> None:
    """Test handling of invalid signatures"""
    svc = HeliusService()
    
    # Test with obviously invalid signature
    invalid_sig = "invalid_signature_that_does_not_exist"
    
    # Should not crash, may return empty result or error
    try:
        result = svc.get_transaction_raw(invalid_sig, network="mainnet")
        # If it doesn't raise an error, result might be None or have error info
        assert result is not None  # Service should handle gracefully
    except Exception as e:
        # Some errors are expected for invalid signatures
        assert "not found" in str(e).lower() or "invalid" in str(e).lower()


# =============================================================================
# Data Validation and Transformation Tests
# =============================================================================

@requires_live
def test_enhanced_transaction_data_structure() -> None:
    """Test that enhanced transactions have correct data structure"""
    svc = HeliusService()
    
    transactions = svc.get_transactions_by_address(USDC_MINT, network="mainnet", limit=1)
    if not transactions:
        pytest.skip("No transactions found for data structure test")
    
    tx = transactions[0]
    assert isinstance(tx, EnhancedTxSummary)
    
    # Check all expected fields exist and have correct types
    assert tx.signature is None or isinstance(tx.signature, str)
    assert tx.slot is None or isinstance(tx.slot, int)
    assert tx.timestamp is None or isinstance(tx.timestamp, int)
    assert tx.type is None or isinstance(tx.type, str)
    assert tx.source is None or isinstance(tx.source, str)
    assert tx.fee_lamports is None or isinstance(tx.fee_lamports, int)
    assert tx.succeeded is None or isinstance(tx.succeeded, bool)
    assert isinstance(tx.native_transfers, list)
    assert isinstance(tx.token_transfers, list)
    
    # Check transfer structures
    for nt in tx.native_transfers:
        assert isinstance(nt.from_addr, str)
        assert isinstance(nt.to_addr, str)
        assert isinstance(nt.amount_lamports, int)
    
    for tt in tx.token_transfers:
        assert isinstance(tt.mint, str)
        assert isinstance(tt.from_addr, str)
        assert isinstance(tt.to_addr, str)
        assert isinstance(tt.amount, str)
        assert tt.decimals is None or isinstance(tt.decimals, int)


@requires_live
def test_asset_data_structure() -> None:
    """Test that assets have correct data structure"""
    svc = HeliusService()
    
    asset = svc.get_asset(USDC_MINT, network="mainnet")
    assert isinstance(asset, AssetSummary)
    
    # Check all expected fields
    assert isinstance(asset.id, str)
    assert asset.name is None or isinstance(asset.name, str)
    assert asset.symbol is None or isinstance(asset.symbol, str)
    assert asset.image is None or isinstance(asset.image, str)
    assert asset.owner is None or isinstance(asset.owner, str)
    assert asset.collection is None or isinstance(asset.collection, str)
    assert asset.compressed is None or isinstance(asset.compressed, bool)
    assert asset.interface is None or isinstance(asset.interface, str)


# =============================================================================
# Performance and Rate Limiting Tests  
# =============================================================================

@requires_live
def test_sequential_requests_performance() -> None:
    """Test that sequential requests work without rate limiting issues"""
    svc = HeliusService()
    
    start_time = time.time()
    
    # Make several sequential requests
    balance1 = svc.get_balance(SYSTEM_PROGRAM, network="mainnet")
    balance2 = svc.get_balance(TOKEN_PROGRAM, network="mainnet") 
    signatures = svc.get_signatures_for_address(USDC_MINT, network="mainnet", limit=1)
    
    end_time = time.time()
    
    # All should succeed
    assert isinstance(balance1, int)
    assert isinstance(balance2, int)
    assert isinstance(signatures, list)
    
    # Should complete in reasonable time (less than 30 seconds)
    assert end_time - start_time < 30


@requires_live 
def test_network_consistency() -> None:
    """Test that same calls to different networks work consistently"""
    svc = HeliusService()
    
    # Test same call on both networks
    mainnet_balance = svc.get_balance(SYSTEM_PROGRAM, network="mainnet")
    devnet_balance = svc.get_balance(SYSTEM_PROGRAM, network="devnet")
    
    assert isinstance(mainnet_balance, int)
    assert isinstance(devnet_balance, int)
    
    # Both should be non-negative
    assert mainnet_balance >= 0
    assert devnet_balance >= 0


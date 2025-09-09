from __future__ import annotations

from helius import transforms as tf


def test_summarize_enhanced_tx_minimal() -> None:
    raw = {
        "signature": "abc",
        "slot": 1,
        "timestamp": 1700000000,
        "type": "TRANSFER",
        "source": "SYSTEM",
        "fee": 5000,
        "status": "success",
        "nativeTransfers": [{"from": "A", "to": "B", "amount": 123}],
        "tokenTransfers": [
            {
                "mint": "M",
                "from": "TA",
                "to": "TB",
                "tokenAmount": {"amount": "10", "decimals": 2},
            }
        ],
    }
    out = tf.summarize_enhanced_tx(raw)
    assert out.signature == "abc"
    assert out.succeeded is True
    assert out.native_transfers[0].amount_lamports == 123
    assert out.token_transfers[0].decimals == 2


def test_summarize_raw_transaction_truncates_logs() -> None:
    logs = [f"log {i}" for i in range(40)]
    tx = {"meta": {"logMessages": logs}, "transaction": {"signatures": ["sig"]}}
    out = tf.summarize_raw_transaction(tx)
    # Our transform keeps 30 lines by truncating early and late slices to 15 each
    assert len(out.log_messages) == 30



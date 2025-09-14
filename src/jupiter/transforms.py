from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple


def comma_join(items: Iterable[str]) -> str:
    return ",".join([s for s in items if isinstance(s, str) and s])


def shape_query(params: Dict[str, Any]) -> Dict[str, Any]:
    # Drop None values to keep requests lean
    return {k: v for k, v in params.items() if v is not None}


def pick_first_nonempty(values: Iterable[Optional[str]]) -> Optional[str]:
    for v in values:
        if isinstance(v, str) and v:
            return v
    return None


def choose_taker_from_whales(
    candidate_addresses: List[str],
) -> Optional[str]:
    # Prefer first candidate (already filtered by service)
    return candidate_addresses[0] if candidate_addresses else None



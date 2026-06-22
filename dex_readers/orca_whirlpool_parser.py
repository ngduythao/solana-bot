
"""Orca Whirlpool parser (scaffold, near-real). 
Fill LAYOUT_OFFSETS by referencing the official Orca Whirlpool account layout.
"""
import base64
from dataclasses import dataclass

# === Replace these offsets with real ones from Orca SDK/docs ===
LAYOUT_OFFSETS = {
    "tick_spacing": (0, 4),         # u32
    "sqrt_price_x64": (8, 16),      # u128 (Q64.64), little-endian
    "liquidity": (24, 16),          # u128
    "fee_tier_bps": (40, 2),        # u16
}

@dataclass
class WhirlpoolState:
    tick_spacing: int
    sqrt_price_x64: int
    liquidity: int
    fee_tier_bps: int

def _le_int(buf: bytes) -> int:
    return int.from_bytes(buf, "little", signed=False)

def parse_whirlpool_account(data_b64: str) -> WhirlpoolState:
    raw = base64.b64decode(data_b64)
    def get(name, default, size_hint=None):
        off, size = LAYOUT_OFFSETS.get(name, (None, None))
        if off is None or off+size > len(raw):
            return default
        return _le_int(raw[off:off+size])
    tick_spacing = get("tick_spacing", 64)
    sqrt_price_x64 = get("sqrt_price_x64", 1<<128-1)  # fallback ~1.0 in Q64.64 (placeholder)
    liquidity = get("liquidity", 0)
    fee_tier_bps = get("fee_tier_bps", 30) or 30
    return WhirlpoolState(tick_spacing, sqrt_price_x64, liquidity, fee_tier_bps)

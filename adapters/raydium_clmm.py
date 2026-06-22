
from dataclasses import dataclass
from typing import List
from .common import get_account_b64

# Placeholder for Raydium CLMM adapter; use config to feed state for now, or extend parser by actual layout later.
@dataclass
class RaydiumPoolState:
    sqrt_price_x64: int
    liquidity: int
    tick_current: int
    fee_bps: int
    tick_spacing: int

@dataclass
class RaydiumTick:
    index: int
    liquidity_net: int

def load_raydium(entry: dict):
    ps = RaydiumPoolState(
        sqrt_price_x64=int(entry.get("sqrtPriceX64", 1<<64)),
        liquidity=int(entry.get("liquidity", 0)),
        tick_current=int(entry.get("tickCurrent", 0)),
        fee_bps=int(entry.get("feeBps", 30)),
        tick_spacing=int(entry.get("tickSpacing", 64)),
    )
    ticks = [RaydiumTick(int(t["index"]), int(t["liquidityNet"])) for t in entry.get("ticks", [])]
    return ps, ticks

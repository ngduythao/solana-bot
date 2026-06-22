
from dataclasses import dataclass
from typing import List
import struct, yaml, os
from .common import get_account_b64

# NOTE: Real Whirlpool layout is complex; this is a minimal reader that expects you to list 'ticks' and 'pool' addresses in config.
# If tick arrays are not provided, we return empty ticks and only pool state from config/defaults.

@dataclass
class WhirlpoolPoolState:
    sqrt_price_x64: int
    liquidity: int
    tick_current: int
    fee_bps: int
    tick_spacing: int

@dataclass
class WhirlpoolTick:
    index: int
    liquidity_net: int

def read_pool_from_config(entry: dict) -> WhirlpoolPoolState:
    # Expect key fields in config: sqrtPriceX64, liquidity, tickCurrent, feeBps, tickSpacing
    return WhirlpoolPoolState(
        sqrt_price_x64=int(entry.get("sqrtPriceX64", 1<<64)),
        liquidity=int(entry.get("liquidity", 0)),
        tick_current=int(entry.get("tickCurrent", 0)),
        fee_bps=int(entry.get("feeBps", 30)),
        tick_spacing=int(entry.get("tickSpacing", 64)),
    )

def read_ticks_from_config(entry: dict) -> List[WhirlpoolTick]:
    arr = []
    for t in entry.get("ticks", []):
        arr.append(WhirlpoolTick(index=int(t["index"]), liquidity_net=int(t["liquidityNet"])))
    return arr

def load_whirlpool(entry: dict):
    pool = read_pool_from_config(entry)
    ticks = read_ticks_from_config(entry)
    return pool, ticks

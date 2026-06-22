
# Whirlpool on-chain parser (skeleton using IDL-like offsets provided in config)
from dataclasses import dataclass
from typing import List, Dict, Any
import struct, json, os
from .idl_common import get_account_b64
from .idl_loader import load_idl_by_name
from .idl_helper import extract_offsets_from_idl

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

def parse_pool(account_data: bytes, layout: Dict[str,int], idl_json: Dict[str,Any]=None) -> WhirlpoolPoolState:
    # layout: offsets for fields (in bytes). You provide via config: e.g. {"sqrtPriceX64": 32, "liquidity": 72, ...}
    layout = extract_offsets_from_idl(idl_json or {}, layout.get("accountName","pool"), layout)
    sqrtP = int.from_bytes(account_data[ layout["sqrtPriceX64"]: layout["sqrtPriceX64"]+16 ], "little", signed=False)
    liq   = int.from_bytes(account_data[ layout["liquidity"]: layout["liquidity"]+16 ], "little", signed=False)
    tickc = int.from_bytes(account_data[ layout["tickCurrent"]: layout["tickCurrent"]+4 ], "little", signed=True)
    fee   = int.from_bytes(account_data[ layout["feeBps"]: layout["feeBps"]+2 ], "little", signed=False)
    tks   = int.from_bytes(account_data[ layout["tickSpacing"]: layout["tickSpacing"]+2 ], "little", signed=False)
    return WhirlpoolPoolState(sqrtP, liq, tickc, fee, tks)

def parse_tick_array(account_data: bytes, entry: Dict[str,Any]) -> List[WhirlpoolTick]:
    # Given tick array account and tickSpacing, construct list of ticks with liquidityNet from array
    # Config must provide: "tickArrayStartIndex", "tickSpacing", and "entrySize", "count"
    out = []
    start = entry.get("tickArrayStartIndex", 0)
    spacing = entry.get("tickSpacing", 64)
    entry_size = entry.get("entrySize", 16)  # bytes per tick entry (liquidityNet i128)
    count = entry.get("count", 88)
    offset = entry.get("dataOffset", 8)  # skip header
    for i in range(count):
        o = offset + i*entry_size
        if o+16 > len(account_data): break
        liq_net = int.from_bytes(account_data[o:o+16], "little", signed=True)
        idx = start + i*spacing
        if liq_net != 0:
            out.append(WhirlpoolTick(index=idx, liquidity_net=liq_net))
    return out

def load_whirlpool_onchain(entry: Dict[str,Any]):
    # entry: {"pool": "<pubkey>", "poolLayout": {...}, "tickArrays": [{"pubkey":..., ...}, ...]}
    pool_acc = get_account_b64(entry["pool"])
    idl = entry.get("idl") or (load_idl_by_name(entry.get("idlName","")) if entry.get("idlName") else None)
    pool = parse_pool(pool_acc, entry["poolLayout"], idl)
    ticks: List[WhirlpoolTick] = []
    for ta in entry.get("tickArrays", []):
        arr_acc = get_account_b64(ta["pubkey"])
        ticks += parse_tick_array(arr_acc, {**ta, "tickSpacing": pool.tick_spacing})
    return pool, ticks

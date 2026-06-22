
# Raydium CLMM on-chain parser (skeleton via config-provided offsets)
from dataclasses import dataclass
from typing import List, Dict, Any
from .idl_common import get_account_b64
from .idl_loader import load_idl_by_name
from .idl_helper import extract_offsets_from_idl

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

def parse_pool(account_data: bytes, layout: Dict[str,int], idl_json: Dict[str,Any]=None) -> RaydiumPoolState:
    layout = extract_offsets_from_idl(idl_json or {}, layout.get("accountName","pool"), layout)
    sqrtP = int.from_bytes(account_data[ layout["sqrtPriceX64"]: layout["sqrtPriceX64"]+16 ], "little", signed=False)
    liq   = int.from_bytes(account_data[ layout["liquidity"]: layout["liquidity"]+16 ], "little", signed=False)
    tickc = int.from_bytes(account_data[ layout["tickCurrent"]: layout["tickCurrent"]+4 ], "little", signed=True)
    fee   = int.from_bytes(account_data[ layout["feeBps"]: layout["feeBps"]+2 ], "little", signed=False)
    tks   = int.from_bytes(account_data[ layout["tickSpacing"]: layout["tickSpacing"]+2 ], "little", signed=False)
    return RaydiumPoolState(sqrtP, liq, tickc, fee, tks)

def parse_tick_page(account_data: bytes, page: Dict[str,Any]) -> List[RaydiumTick]:
    # page: {"startIndex":..., "entrySize": 16, "count": 256, "dataOffset": 0}
    out=[]
    start = page.get("startIndex", 0)
    spacing = page.get("tickSpacing", 64)
    entry_size = page.get("entrySize", 16)
    count = page.get("count", 256)
    offset = page.get("dataOffset", 0)
    for i in range(count):
        o = offset + i*entry_size
        if o+16 > len(account_data): break
        liq_net = int.from_bytes(account_data[o:o+16], "little", signed=True)
        idx = start + i*spacing
        if liq_net != 0:
            out.append(RaydiumTick(idx, liq_net))
    return out

def load_raydium_onchain(entry: Dict[str,Any]):
    pool_acc = get_account_b64(entry["pool"])
    idl = entry.get("idl") or (load_idl_by_name(entry.get("idlName","")) if entry.get("idlName") else None)
    pool = parse_pool(pool_acc, entry["poolLayout"], idl)
    ticks: List[RaydiumTick] = []
    for pg in entry.get("tickPages", []):
        acc = get_account_b64(pg["pubkey"])
        ticks += parse_tick_page(acc, {**pg, "tickSpacing": pool.tick_spacing})
    return pool, ticks

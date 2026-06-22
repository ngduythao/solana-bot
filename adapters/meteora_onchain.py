
# Meteora DLMM on-chain parser (skeleton via config-provided bin layout)
from dataclasses import dataclass
from typing import List, Dict, Any
from .idl_common import get_account_b64
from .idl_loader import load_idl_by_name
from .idl_helper import extract_offsets_from_idl

@dataclass
class Bin:
    price_q64: int
    liq_q0: int

@dataclass
class MeteoraState:
    bins: List[Bin]
    fee_bps: int

def parse_bins(account_data: bytes, layout: Dict[str,int]) -> List[Bin]:
    # layout: {"count":..., "entrySize":..., "offsetPrice":..., "offsetLiquidity":..., "stride":...}
    out=[]
    count = layout.get("count", 64)
    stride = layout.get("stride", layout.get("entrySize", 32))
    offP = layout.get("offsetPrice", 0)
    offL = layout.get("offsetLiquidity", 16)
    base = layout.get("dataOffset", 0)
    for i in range(count):
        o = base + i*stride
        if o+max(offP+16, offL+16) > len(account_data): break
        price = int.from_bytes(account_data[o+offP:o+offP+16], "little", signed=False)
        liq   = int.from_bytes(account_data[o+offL:o+offL+16], "little", signed=False)
        if liq != 0:
            out.append(Bin(price, liq))
    return out

def load_meteora_onchain(entry: Dict[str,Any]):
    fee_bps = int(entry.get("feeBps", 30))
    acc = get_account_b64(entry["lob"])
    bins = parse_bins(acc, entry["binLayout"])
    return MeteoraState(bins=bins, fee_bps=fee_bps)

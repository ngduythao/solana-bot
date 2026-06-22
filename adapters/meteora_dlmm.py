
from dataclasses import dataclass
from typing import List
from .common import get_account_b64

@dataclass
class Bin:
    price_q64: int
    liq_q0: int

@dataclass
class MeteoraState:
    bins: List[Bin]
    fee_bps: int

def load_meteora(entry: dict):
    fee_bps = int(entry.get("feeBps", 30))
    bins = [Bin(int(b["priceQ64"]), int(b["liqQ0"])) for b in entry.get("bins", [])]
    return MeteoraState(bins=bins, fee_bps=fee_bps)

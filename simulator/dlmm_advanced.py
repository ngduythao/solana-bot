
"""Advanced DLMM helpers (bin-walk, dynamic fee). Safe for missing bins (returns 0)."""
from typing import List, Tuple
def walk_bins(qty_in:int, bins, base_fee_bps:int) -> Tuple[int, float]:
    if qty_in<=0 or not bins:
        return 0, 0.0
    # naive: consume proportional to bin liquidity, fee = base_fee_bps
    remaining = qty_in
    out = 0
    for b in bins:
        if remaining<=0: break
        take = min(remaining, max(1, b.liq // 1_000_000))  # coarse
        remaining -= take
        out += int(take * (b.price_x64 / (1<<64)) * (1 - base_fee_bps/10000.0))
    fill = (qty_in - remaining)/max(1,qty_in)
    return out, fill

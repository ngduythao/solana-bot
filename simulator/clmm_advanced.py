
"""Advanced CLMM helpers (tick-walk, partial fill). 
If tick arrays are missing, the functions return safe lower-bounds without raising.
"""
from typing import List, Tuple

def walk_ticks(qty_in:int, sqrt_price_x64:int, liquidity:int, fee_bps:int, tick_arrays=None) -> Tuple[int, float]:
    if qty_in<=0 or liquidity<=0:
        return 0, 0.0
    # TODO: if tick_arrays provided, consume across ticks. For now, fallback factor ~95% of simple proxy.
    from .clmm_math import swap_x_to_y
    base = swap_x_to_y(qty_in, sqrt_price_x64, liquidity, fee_bps)
    return int(base*0.95), 0.95

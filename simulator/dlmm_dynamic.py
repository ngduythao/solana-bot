
"""DLMM dynamic bins: walk bins with dynamic fee function.
Inputs:
- qty_in: int
- bins: list[dict] with {'price_x64': int, 'liq': int}
- base_fee_bps: int
- fee_fn: optional callable(b:dict, congestion:float)->bps
- order: 'near_first' or 'liq_desc'
Returns (out:int, fill_ratio:float)
"""
from typing import List, Tuple, Callable

def walk_bins(qty_in:int, bins:List[dict], base_fee_bps:int, fee_fn:Callable=None, order:str='near_first', congestion:float=0.0)->Tuple[int,float]:
    if qty_in<=0 or not bins: return 0, 0.0
    if order=='liq_desc':
        bins = sorted(bins, key=lambda b: b['liq'], reverse=True)
    out = 0; rem = qty_in
    for b in bins:
        if rem<=0: break
        fee = base_fee_bps
        if fee_fn: fee = int(fee_fn(b, congestion))
        take = min(rem, b['liq'])
        rem -= take
        out += int(take * (b['price_x64']/(1<<64)) * (1 - fee/10000.0))
    return out, (qty_in-rem)/qty_in

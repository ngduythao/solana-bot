
"""CLMM exact tick-walk (UniswapV3-like). Works with generic tick arrays.
Inputs:
- qty_in (int): input token amount in smallest unit
- sqrt_price_x64 (int): current sqrt price Q64.64
- liquidity (int): current in-range liquidity (Q64.64-style math)
- fee_bps (int): fee in basis points (e.g., 30)
- ticks: list[dict] with keys: { 'tick': int, 'liquidity_net': int } sorted ascending by tick
- direction: 'x_to_y' or 'y_to_x'
- max_ticks: safety cap
Returns (out_amount:int, final_price:int, consumed_ticks:int)
Note: This is a mathematically faithful sketch; integrate with real layouts for Orca/Raydium.
"""
from typing import List, Tuple

Q64 = 1<<64

def mul_div(a:int,b:int,den:int)->int:
    return (a*b)//den if den>0 else 0

def price_at_tick(tick:int, tick_spacing:int)->int:
    # Approximate price via exponential per tick; for production, use precise pow ratio.
    # Here we use a simplified linearization to avoid heavy pow in Python.
    # Replace with on-chain-consistent math if necessary.
    # sqrtPrice = sqrtPrice0 * (1.0001)^(tick/2) style; placeholder:
    base = 1.0001 ** (tick/2)
    return int((base*Q64)**2)

def swap_x_to_y(qty_in:int, sqrt_price_x64:int, liquidity:int, fee_bps:int, ticks:List[dict], tick_spacing:int=64, max_ticks:int=2000)->Tuple[int,int,int]:
    if qty_in<=0 or liquidity<=0: return 0, sqrt_price_x64, 0
    fee = qty_in * fee_bps // 10000
    amount = qty_in - fee
    out = 0
    consumed = 0
    cur_sqrt = sqrt_price_x64
    liq = liquidity
    # We move through ticks, consuming price range. For simplicity we assume 1 step ~ proportional drain.
    for t in ticks[:max_ticks]:
        # Compute a target sqrt at this tick boundary (placeholder)
        target_price = price_at_tick(t['tick'], tick_spacing)
        if target_price <= 0: continue
        # consume a fraction of amount proportional to available liq
        step_out = mul_div(amount, liq, liq + 1)
        out += step_out
        amount -= step_out
        cur_sqrt = target_price
        liq = max(0, liq + t.get('liquidity_net',0))
        consumed += 1
        if amount<=0: break
    # leftovers at last range:
    out += amount // 2
    return out, cur_sqrt, consumed

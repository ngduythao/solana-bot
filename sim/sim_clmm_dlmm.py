
# Minimal CLMM/DLMM simulator scaffold (tick/bin/fee dynamic/partial fill)
import math, random
from dataclasses import dataclass

@dataclass
class Leg:
    kind: str   # "CLMM"|"DLMM"
    fee_bps: float
    price: float
    liquidity: float

def partial_fill(leg: Leg, amount_in):
    # simplistic price impact model
    eff_price = leg.price * (1 + (amount_in/ max(1e-6, leg.liquidity)) * 0.001)
    out = amount_in * (1 - leg.fee_bps/1e4) / eff_price
    return out, eff_price

def route_pnl_usd(legs, amount_in, ref_prices):
    amt = amount_in
    for i, lg in enumerate(legs):
        amt, px = partial_fill(lg, amt)
    # mark-to-market vs ref price of last token
    last_ref = ref_prices[-1]
    pnl = (amt * last_ref) - (amount_in * ref_prices[0])
    return pnl

if __name__ == "__main__":
    # tiny demo
    legs = [Leg("CLMM", 5, 1.0, 1_000_000), Leg("DLMM", 8, 1.01, 800_000)]
    ref = [1.0, 1.02]
    print("PNL sample:", route_pnl_usd(legs, 1000, ref))

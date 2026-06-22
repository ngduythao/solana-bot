
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class Bin:
    price_q64: int     # price in Q64.64 (tokenB per tokenA)
    liq_q0: int        # available tokenA (a2b) or tokenB (b2a)

@dataclass
class DLMMState:
    bins: List[Bin]
    fee_bps: int

@dataclass
class DLMMResult:
    amount_in: int
    amount_out: int
    fee_paid: int
    bins_used: int

Q64 = 1<<64

def simulate_dlmm_exact_in(state: DLMMState, amount_in: int, a2b: bool) -> DLMMResult:
    remain = amount_in
    out = 0
    fee_total = 0
    used = 0

    # For determinism, assume bins ordered best->worse for target direction
    bins = state.bins[:]

    for b in bins:
        if remain <= 0: break
        fee = (remain * state.fee_bps) // 10000
        after = remain - fee
        take = min(after, b.liq_q0)
        if take <= 0: continue

        if a2b:
            # out = take * price
            out += (take * b.price_q64) >> 64
        else:
            # buying A with B: out (tokenA) = take / price
            out += (take << 64) // max(1, b.price_q64)
        fee_total += (take * state.fee_bps) // 10000
        remain -= (take + (take * state.fee_bps) // 10000)
        used += 1

    return DLMMResult(amount_in=amount_in - remain, amount_out=out, fee_paid=fee_total, bins_used=used)

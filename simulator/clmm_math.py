
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

# Deterministic Q64.64 math (integers only). Avoid float/Decimal for consistency across runs.
Q64 = 1 << 64
ONE = Q64

def mul_q64(a: int, b: int) -> int:
    return (a * b) >> 64

def div_q64(a: int, b: int) -> int:
    return (a << 64) // b

# Precompute constants for 1.0001^(2^i) in Q64.64 to do exponentiation by squaring (like Uniswap v3 reference).
# Values below are rounded to nearest Q64.64 fixed-point. (Short list sufficient for typical tick ranges.)
# These can be extended if you simulate extreme ticks.
POW_1_0001_Q64 = [
    0x10000000000000000,  # 1.0001^(1)   ^0 placeholder (actually 1.0) kept for alignment
    0x10000000000028F5C,  # 1.0001^(2^0)
    0x1000000000051EB85,  # 1.0001^(2^1)
    0x1000000000A3D70A,   # 2^2
    0x10000000147AE147,   # 2^3
    0x100000028F5C28F6,   # 2^4
    0x10000051EB851EC,    # 2^5
    0x100000A3D70A3D8,    # 2^6
    0x10000147AE147B,     # 2^7
    0x1000028F5C28F7,     # 2^8
    0x1000051EB851F0,     # 2^9
    0x10000A3D70A3E2,     # 2^10
    0x1000147AE147C7,     # 2^11
    0x100028F5C28F95,     # 2^12
    0x100051EB851F2B,     # 2^13
    0x1000A3D70A3E56,     # 2^14
    0x100147AE147CAC,     # 2^15
]

def pow_1_0001_to_tick_half_q64(tick_half: int) -> int:
    # returns (1.0001)^(tick_half) in Q64.64 using exponentiation by squaring
    x = ONE
    y = 0x10000000000028F5C  # 1.0001^(1) in Q64.64 (approx)
    t = abs(tick_half)
    i = 1
    while t > 0 and i < len(POW_1_0001_Q64):
        if t & 1:
            x = mul_q64(x, y)
        y = mul_q64(y, y)
        t >>= 1
        i += 1
    if tick_half < 0:
        x = div_q64(ONE, x)
    return x

def tick_to_sqrt_price_q64(tick: int) -> int:
    # sqrt(P) = 1.0001^(tick/2)
    return pow_1_0001_to_tick_half_q64(tick)

@dataclass
class Tick:
    index: int            # tick index
    liquidity_net: int    # signed, Q0 (lamports liquidity units)

@dataclass
class PoolState:
    sqrt_price_x64: int   # Q64.64
    liquidity: int        # Q0 (liquidity in token terms scaled, as per Whirlpool)
    tick_current: int
    fee_bps: int
    tick_spacing: int

@dataclass
class SwapResult:
    amount_in: int
    amount_out: int
    fee_paid: int
    crossed: int
    est_cu: int
    final_sqrt_price_x64: int
    final_tick: int

def _consume_a2b(L: int, S: int, dx: int, boundary_Q: int) -> Tuple[int,int,int]:
    # dx (token A in), L (liquidity), S (sqrtP) and boundary_Q are Q64.64 or Q0 as annotated:
    # Uniswap v3 exact-in formula in fixed point:
    # Q = (L*S) / (L + dx*S) ; Δy = L*(S - Q) ; Δx used may be < dx if hitting boundary
    LS = L * S                       # Q64 * Q0 = Q64 scaled -> treat as 128-bit then >> 64 when needed
    denom = L + ((dx * S) >> 64)
    if denom == 0: return S, 0, 0
    Q = LS // denom
    if Q < boundary_Q:
        Q = boundary_Q
        # recompute used Δx when clamped at boundary
        # Δx = L*(S-Q)/(S*Q)  => Δx = L * (S-Q) / (S*Q)
        num = L * (S - Q)
        den = (S * Q) >> 64
        used_dx = (num << 64) // max(1, den)
    else:
        used_dx = dx
    dy = (L * (S - Q))               # still Q64.64 scaled
    dy = dy >> 64
    return Q, dy, used_dx

def _consume_b2a(L: int, S: int, dy: int, boundary_Q: int) -> Tuple[int,int,int]:
    # token B in; Q = S + dy/L ; Δx = L*(Q-S)/(Q*S)
    add = (dy << 64) // max(1, L)
    Q = S + add
    if Q > boundary_Q:
        Q = boundary_Q
        # used Δy = L*(Q - S)
        used_dy = (L * (Q - S)) >> 64
    else:
        used_dy = dy
    num = L * (Q - S)
    den = (Q * S) >> 64
    dx = (num << 64) // max(1, den)
    return Q, dx, used_dy

def next_tick_index(cur: int, spacing: int, a2b: bool) -> int:
    mod = cur % spacing
    if a2b:
        return cur - (mod if mod >= 0 else (mod + spacing)) - spacing
    else:
        return cur - (mod if mod >= 0 else (mod + spacing)) + spacing

def simulate_whirlpool_exact_in(pool: PoolState, ticks: List[Tick], amount_in: int, a2b: bool, min_out: int = 0) -> SwapResult:
    tick_map = {t.index: t for t in ticks}
    L = pool.liquidity
    S = pool.sqrt_price_x64
    cur_tick = pool.tick_current
    spacing = pool.tick_spacing
    fee_bps = pool.fee_bps

    remain_in = amount_in
    total_out = 0
    total_fee = 0
    crossed = 0

    while remain_in > 0 and L > 0:
        nxt_tick = next_tick_index(cur_tick, spacing, a2b)
        boundary_Q = tick_to_sqrt_price_q64(nxt_tick)

        fee = (remain_in * fee_bps) // 10000
        amt_after_fee = remain_in - fee

        if a2b:
            Q, dy, used_in = _consume_a2b(L, S, amt_after_fee, boundary_Q)
            used_fee = (used_in * fee_bps) // 10000
            total_fee += used_fee
            total_out += dy
            remain_in -= (used_in + used_fee)
        else:
            Q, dx, used_in = _consume_b2a(L, S, amt_after_fee, boundary_Q)
            used_fee = (used_in * fee_bps) // 10000
            total_fee += used_fee
            total_out += dx
            remain_in -= (used_in + used_fee)

        S = Q

        at_boundary = (S == boundary_Q)
        if at_boundary:
            crossed += 1
            cur_tick = nxt_tick
            liq_net = tick_map.get(nxt_tick).liquidity_net if nxt_tick in tick_map else 0
            # Crossing convention: upward adds, downward subtracts
            L = L + (liq_net if not a2b else -liq_net)
            if L <= 0:
                break
        else:
            break

        if min_out > 0 and total_out >= min_out:
            break

        if crossed > 20000:
            break

    est_cu = 150000 + crossed * 18000
    return SwapResult(
        amount_in=amount_in - remain_in,
        amount_out=total_out,
        fee_paid=total_fee,
        crossed=crossed,
        est_cu=est_cu,
        final_sqrt_price_x64=S,
        final_tick=cur_tick,
    )

def partial_fill(price,qty,tick_spacing=1):
    # simple model of partial fill based on tick spacing
    filled=qty*0.9
    leftover=qty-filled
    return filled,leftover

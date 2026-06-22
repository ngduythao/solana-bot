
# FastAPI simulator for CLMM (Orca/Raydium) and DLMM (Meteora).
# Accepts pool snapshots + swap amount and returns expected out, fees, ticks crossed.
# This server is stateless and can be scaled independently.
import math, os
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

app=FastAPI(title="Solana Bot Simulator", version="1.0")

# === Models ===
class ClmmState(BaseModel):
    sqrt_price_x64: int
    liquidity: int
    tick_current: int
    fee_bps: int
    tick_spacing: int
    # tick arrays: list of [tick_index, liquidity_net]
    ticks: List[List[int]] = []

class DlmmBin(BaseModel):
    price: float
    liq: float
    fee_bps: int

class SimClmmReq(BaseModel):
    state: ClmmState
    amount_in: int
    is_token_a_in: bool
    limit_tick: Optional[int] = None

class SimClmmRes(BaseModel):
    amount_out: int
    amount_in_consumed: int
    fee_paid: int
    ticks_crossed: int
    new_sqrt_price_x64: int
    new_tick: int

class SimDlmmReq(BaseModel):
    bins: List[DlmmBin]
    amount_in: float
    is_base_in: bool

class SimDlmmRes(BaseModel):
    amount_out: float
    fee_paid: float
    bins_used: int

# === Helpers ===
Q64 = 1<<64
def tick_to_sqrtp(tick:int)->int:
    # simplified conversion: sqrt(1.0001^tick) * 2^64
    return int((1.0001**(tick/2.0)) * Q64)

def clmm_swap_exact_in(state: ClmmState, amount_in:int, is_a_in:bool, limit_tick: Optional[int])->SimClmmRes:
    sqrtp = state.sqrt_price_x64
    L = state.liquidity
    fee_bps = state.fee_bps
    tick = state.tick_current
    spacing = state.tick_spacing
    ticks = {ti:ln for ti,ln in state.ticks} if state.ticks else {}

    remain = amount_in
    out_total = 0
    fee_total = 0
    ticks_crossed = 0

    direction = -1 if is_a_in else 1  # placeholder convention

    while remain>0 and L>0:
        next_tick = tick + (direction*spacing)
        if limit_tick is not None:
            if (direction>0 and next_tick>limit_tick) or (direction<0 and next_tick<limit_tick):
                next_tick = limit_tick

        next_sqrtp = max(1, tick_to_sqrtp(next_tick))

        if is_a_in:
            dx_max = int(((L * (next_sqrtp - sqrtp)) // Q64))
            if dx_max<=0: break
            dx_with_fee = int(dx_max * (1 + fee_bps/1e4))
            if remain < dx_with_fee:
                dx_no_fee = int(remain / (1 + fee_bps/1e4))
                dy = int((L * dx_no_fee * Q64) // max(sqrtp * next_sqrtp,1))
                out_total += dy
                fee_total += remain - dx_no_fee
                remain = 0
                # approximate move
                frac = dx_no_fee / max(dx_max,1)
                sqrtp = int(sqrtp + (next_sqrtp - sqrtp) * frac)
            else:
                remain -= dx_with_fee
                dy = int((L * (next_sqrtp - sqrtp)) // Q64)
                out_total += dy
                fee_total += dx_with_fee - dx_max
                sqrtp = next_sqrtp
                tick = next_tick
                if tick in ticks: L = max(0, L + ticks[tick])
                ticks_crossed += 1
        else:
            dy_max = int((L * (sqrtp - next_sqrtp)) // Q64)
            if dy_max<=0: break
            dy_with_fee = int(dy_max * (1 + fee_bps/1e4))
            if remain < dy_with_fee:
                dy_no_fee = int(remain / (1 + fee_bps/1e4))
                dx = int((L * dy_no_fee) // Q64)
                out_total += dx
                fee_total += remain - dy_no_fee
                remain = 0
                frac = dy_no_fee / max(dy_max,1)
                sqrtp = int(sqrtp - (sqrtp - next_sqrtp) * frac)
            else:
                remain -= dy_with_fee
                dx = int((L * (sqrtp - next_sqrtp)) // Q64)
                out_total += dx
                fee_total += dy_with_fee - dy_max
                sqrtp = next_sqrtp
                tick = next_tick
                if tick in ticks: L = max(0, L + ticks[tick])
                ticks_crossed += 1

        if limit_tick is not None and tick == limit_tick and remain>0:
            break

    return SimClmmRes(
        amount_out=int(out_total),
        amount_in_consumed=amount_in-remain,
        fee_paid=int(fee_total),
        ticks_crossed=ticks_crossed,
        new_sqrt_price_x64=int(sqrtp),
        new_tick=int(tick)
    )

def dlmm_swap_exact_in(bins: List[DlmmBin], amount_in: float, is_base_in: bool)->SimDlmmRes:
    amt = amount_in
    out=0.0; fee=0.0; used=0
    for b in bins:
        if amt<=0: break
        used += 1
        take = min(amt, b.liq)
        gross = take * b.price if is_base_in else take / max(b.price,1e-12)
        fee_inc = gross * (b.fee_bps/1e4)
        fee += fee_inc
        out += (gross - fee_inc)
        amt -= take
    return SimDlmmRes(amount_out=out, fee_paid=fee, bins_used=used)

@app.post("/simulate/clmm", response_model=SimClmmRes)
def simulate_clmm(req: SimClmmReq):
    return clmm_swap_exact_in(req.state, req.amount_in, req.is_token_a_in, req.limit_tick)

@app.post("/simulate/dlmm", response_model=SimDlmmRes)
def simulate_dlmm(req: SimDlmmReq):
    return dlmm_swap_exact_in(req.bins, req.amount_in, req.is_base_in)

from readers.pool_reader import read_orca_clmm_state, read_raydium_clmm_state, read_meteora_dlmm_bins
import httpx

@app.get("/snapshot/clmm/orca")
def snapshot_orca(pool_pk: str):
    with httpx.Client() as c:
        return read_orca_clmm_state(c, pool_pk)

@app.get("/snapshot/clmm/raydium")
def snapshot_raydium(pool_pk: str):
    with httpx.Client() as c:
        return read_raydium_clmm_state(c, pool_pk)

@app.get("/snapshot/dlmm/meteora")
def snapshot_meteora(pool_pk: str):
    with httpx.Client() as c:
        return {"bins": read_meteora_dlmm_bins(c, pool_pk)}

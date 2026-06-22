
from simulator.sim_server import clmm_swap_exact_in, ClmmState, dlmm_swap_exact_in, DlmmBin

def test_clmm_monotonic_small_amt():
    st=ClmmState(sqrt_price_x64=2**64, liquidity=10_000_000, tick_current=0, fee_bps=30, tick_spacing=64, ticks=[])
    res1=clmm_swap_exact_in(st, 100, True, None)
    res2=clmm_swap_exact_in(st, 200, True, None)
    assert res2.amount_out >= res1.amount_out

def test_dlmm_bins_consumption():
    bins=[DlmmBin(price=1.0, liq=10, fee_bps=30), DlmmBin(price=1.01, liq=10, fee_bps=30)]
    res=dlmm_swap_exact_in(bins, 15, True)
    assert res.bins_used == 2

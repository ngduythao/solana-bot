
import os, time, json, redis
from simulator.clmm_math import simulate_whirlpool_exact_in, PoolState as WPState, Tick as WPTick
from adapters.whirlpool import load_whirlpool
from adapters.raydium_clmm import load_raydium
from adapters.meteora_dlmm import load_meteora
from simulator.dlmm_math import simulate_dlmm_exact_in, DLMMState, Bin as DLMMBin

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

def write_est(key, val):
    r.setex(key, 30, json.dumps(val))

def loop_once():
    # Read selection prepared by upstream (preselector) for a pair
    sel = r.get("solbot:preselector:current")
    if not sel: return
    s = json.loads(sel)
    # Use adapter config snapshot from Redis (or fallback to static config later)
    entry = s.get("adapter_entry") or {}
    dex = entry.get("dex","JUPITER")
    if dex in ("WHIRLPOOL","ORCA"):
        ps, ticks = load_whirlpool(entry)
        res = simulate_whirlpool_exact_in(
            WPState(ps.sqrt_price_x64, ps.liquidity, ps.tick_current, ps.fee_bps, ps.tick_spacing),
            [WPTick(t.index, t.liquidity_net) for t in ticks],
            amount_in=int(s.get("amount_in", 1_000_000)),
            a2b=bool(s.get("a2b", True)),
            min_out=int(s.get("min_out", 0)),
        )
        write_est("solbot:cu_estimate", {"cu": res.est_cu, "min_out": res.amount_out})
    elif dex in ("RAYDIUM","CLMM"):
        ps, ticks = load_raydium(entry)
        res = simulate_whirlpool_exact_in(
            WPState(ps.sqrt_price_x64, ps.liquidity, ps.tick_current, ps.fee_bps, ps.tick_spacing),
            [WPTick(t.index, t.liquidity_net) for t in ticks],
            amount_in=int(s.get("amount_in", 1_000_000)),
            a2b=bool(s.get("a2b", True)),
            min_out=int(s.get("min_out", 0)),
        )
        write_est("solbot:cu_estimate", {"cu": res.est_cu, "min_out": res.amount_out})
    elif dex in ("METEORA","DLMM"):
        st = load_meteora(entry)
        res = simulate_dlmm_exact_in(
            DLMMState(bins=[DLMMBin(b.price_q64, b.liq_q0) for b in st.bins], fee_bps=st.fee_bps),
            amount_in=int(s.get("amount_in", 1_000_000)),
            a2b=bool(s.get("a2b", True)),
        )
        write_est("solbot:cu_estimate", {"cu": 130000 + res.bins_used*15000, "min_out": res.amount_out})
    else:
        # Fallback
        write_est("solbot:cu_estimate", {"cu": 180000, "min_out": 0})

def main():
    print("[cu_estimator] running; writing solbot:cu_estimate")
    while True:
        try:
            loop_once()
        except Exception as e:
            print("[cu_estimator] err:", e)
        time.sleep(1.0)

if __name__ == "__main__":
    main()


import os, time, json, redis, math

r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def score_route(pool, mid_q64:int, size_q0:int):
    # Placeholder: score using liquidity hint and fee tier
    try:
        e = json.loads(r.get("solbot:adapter_entry:last") or b"{}")
        fee_bps = e.get("feeBps", 30)
        liq = 1
        if "ticks" in e: liq = max(1, sum(abs(t.get("liquidityNet",0)) for t in e["ticks"][:8]))
        if "bins" in e: liq = max(1, sum(int(b.get("liqQ0",0)) for b in e["bins"][:8]))
        ev = (size_q0/1e6) * max(0.1, math.log1p(liq)) - fee_bps*10
        return ev
    except Exception: return 0.0

def choose_best_route(candidates, mid_q64:int, size_q0:int):
    best=None; best_ev=-1e18
    for pool in candidates:
        ev = score_route(pool, mid_q64, size_q0)
        if ev>best_ev: best_ev, best = ev, pool
    return best, best_ev

def main():
    print("[pre_sim++] running")
    while True:
        try:
            req_raw = r.lindex("solbot:bundle_plans", 0)
            if req_raw:
                j = json.loads(req_raw)
                pools = j.get("pools", ["SOL/USDC.whirlpool", "SOL/USDC.raydium"])
                best, ev = choose_best_route(pools, int(j.get("mid_q64",1<<64)), int(j.get("size_q0",1_000_000)))
                j["best_pool"]=best; j["ev_hint"]=ev
                r.lset("solbot:bundle_plans", 0, json.dumps(j))
        except Exception:
            pass
        time.sleep(1.0)

if __name__ == "__main__":
    main()


stop=False

def _stop_sig(*_):
    global stop; stop=True
signal.signal(signal.SIGTERM, _stop_sig)
signal.signal(signal.SIGINT, _stop_sig)
import signal, sys

import os, time, json, math, redis
from adapters.phoenix_instr import make_place_order_ix as phx_place
from adapters.openbook_instr import make_place_order_ix as ob_place

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

HEDGE_THRESH = float(os.getenv("HEDGE_THRESH","0.02"))   # 2% NAV deviation
MIN_SPREAD   = float(os.getenv("HEDGE_MIN_SPREAD","0.0008"))
MAX_SIZE_Q0  = int(os.getenv("HEDGE_MAX_SIZE_Q0","5000000"))  # 5 units w/ 6 decimals
ORDER_TTL_S  = int(os.getenv("HEDGE_ORDER_TTL_S","10"))

def _liq_hint(pair):
    # read simulated liquidity around mid from adapter_entry ticks/bins if available
    try:
        cur = json.loads(r.get("solbot:adapter_entry:last") or b"{}")
        # crude: total liquidity absolute
        if "ticks" in cur:
            return max(1, sum(abs(t.get("liquidityNet",0)) for t in cur.get("ticks",[])[:8]))
        if "bins" in cur:
            return max(1, sum(int(b.get("liqQ0",0)) for b in cur.get("bins",[])[:8]))
    except Exception:
        pass
    return 1

def _size_from_spread(spread_bps, liq):
    # bigger size when spread tight and liquidity higher
    s = MAX_SIZE_Q0 * min(1.0, (liq/1e9)) * max(0.3, 1.0 - spread_bps/20.0)
    return max(1, int(s))

def _push_req(ix, market, owner, price_q64, size_q0, side):
    if not ix: return
    r.lpush("autohedge:ix_req", json.dumps({
        "market": market, "owner": owner, "price_q64": int(price_q64),
        "size_q0": int(size_q0), "side": side, "ts": time.time()
    }))
    r.ltrim("autohedge:ix_req", 0, 499)

def main():
    print("[autohedge2] running")
    last_order = None  # track last order params
    last_ts = 0
    while not stop:
        try:
            inv = json.loads(r.get("solbot:inventory:state") or b"{}")
            pair = inv.get("pair","SOL/USDC")
            owner = inv.get("owner","MakerOwner1111111111111111111111111111111")
            market = inv.get("market","Market11111111111111111111111111111111")
            nav_dev = float(inv.get("nav_deviation",0.0))
            mid_q64 = int(inv.get("price_q64", 1<<64))
            spread_bps = float(inv.get("spread_bps", 10.0))
            liq = _liq_hint(pair)
            if abs(nav_dev) >= HEDGE_THRESH and spread_bps >= MIN_SPREAD*10000:
                side = "sell" if nav_dev>0 else "buy"
                size = _size_from_spread(spread_bps, liq)
                # Replace if params changed materially or TTL exceeded
                need_new = True
                if last_order:
                    changed = (last_order["side"]!=side) or (abs(last_order["size"]-size)>MAX_SIZE_Q0*0.2)
                    ttl = (time.time()-last_ts)>ORDER_TTL_S
                    need_new = changed or ttl
                if need_new:
                    ix = phx_place(market, owner, mid_q64, size, side) or ob_place(market, owner, mid_q64, size, side)
                    _push_req(ix, market, owner, mid_q64, size, side)
                    last_order = {"side":side, "size":size}
                    last_ts = time.time()
                    r.lpush("autohedge:plan", json.dumps({"pair":pair,"side":side,"size":size,"spread_bps":spread_bps,"liq_hint":liq,"ts":last_ts}))
                    r.ltrim("autohedge:plan", 0, 199)
            else:
                # cancel/skip by doing nothing (executor may eventually expire)
                pass
        except Exception as e:
            print("[autohedge2] err:", e)
        time.sleep(1.0)

if __name__ == "__main__":
    main()

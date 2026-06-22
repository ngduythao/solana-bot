
import os, time, json, httpx, redis

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

DQ_CEX=os.getenv("DQ_CEX","hb:dispatch:cex")
SYMS=[s.strip() for s in os.getenv("BASIS_SYMBOLS","BTCUSDT,ETHUSDT,SOLUSDT").split(",") if s.strip()]
BASIS_THR=float(os.getenv("BASIS_THR_BPS","15")) # 15 bps
ENABLE = os.getenv("ENABLE_CEX_BASIS","false").lower()=="true"
TRADE_ENABLE = os.getenv("ENABLE_CEX_TRADING","false").lower()=="true"

def bn_spot(client, sym):
    res=client.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": sym}, timeout=2); res.raise_for_status()
    return float(res.json()["price"])

def bn_perp(client, sym):
    res=client.get("https://fapi.binance.com/fapi/v1/ticker/price", params={"symbol": sym}, timeout=2); res.raise_for_status()
    return float(res.json()["price"])

def run():
    if not ENABLE:
        while True:
            time.sleep(15)
    with httpx.Client() as c:
        while True:
            for sym in SYMS:
                try:
                    sp = bn_spot(c, sym)
                    pp = bn_perp(c, sym)
                    spread_bps = (pp - sp) / max(sp,1e-9) * 1e4
                    r.hset("basis:spread_bps", sym, round(spread_bps,2))
                    if abs(spread_bps) >= BASIS_THR:
                        side = "SHORT_PERP_LONG_SPOT" if spread_bps>0 else "LONG_PERP_SHORT_SPOT"
                        r.lpush(DQ_CEX, json.dumps({
                            "type":"CEX_BASIS_ARBIT",
                            "symbol": sym,
                            "side": side,
                            "spread_bps": round(spread_bps,2),
                            "dry": not TRADE_ENABLE
                        }))
                except Exception as e:
                    r.hset("basis:error", sym, str(e))
            time.sleep(3)

if __name__=="__main__":
    run()

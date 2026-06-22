
import os, time, math, json, httpx, redis
from datetime import datetime, timezone

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

DQ_CEX=os.getenv("DQ_CEX","hb:dispatch:cex")
SYMS=[s.strip() for s in os.getenv("FUNDING_SYMBOLS","BTCUSDT,ETHUSDT,SOLUSDT").split(",") if s.strip()]
VENUES=[s.strip().upper() for s in os.getenv("FUNDING_VENUE","BINANCE,BYBIT").split(",") if s.strip()]
APR_MIN=float(os.getenv("FUNDING_MIN_APR","0.10"))  # 10% APR
COOLDOWN_SEC=int(os.getenv("FUNDING_COOLDOWN_SEC","300"))
ENABLE = os.getenv("ENABLE_CEX_FUNDING","false").lower()=="true"
TRADE_ENABLE = os.getenv("ENABLE_CEX_TRADING","false").lower()=="true"

def apr_from_rate(rate_8h: float)->float:
    return rate_8h * 3 * 365

def binance_funding(sym):
    url="https://fapi.binance.com/fapi/v1/premiumIndex"
    with httpx.Client() as c:
        res=c.get(url, params={"symbol": sym}, timeout=2); res.raise_for_status()
        d=res.json()
        rate=float(d.get("lastFundingRate") or 0.0)
        mark=float(d.get("markPrice") or 0.0)
        return {"venue":"BINANCE","rate_8h":rate,"mark":mark}

def bybit_funding(sym):
    url="https://api.bybit.com/v5/market/tickers"
    with httpx.Client() as c:
        res=c.get(url, params={"category":"linear","symbol": sym}, timeout=2); res.raise_for_status()
        lst=res.json().get("result",{}).get("list",[])
        if not lst: return {"venue":"BYBIT","rate_8h":0.0,"mark":0.0}
        it=lst[0]
        fr_api="https://api.bybit.com/v5/market/funding/history"
        fr=c.get(fr_api, params={"category":"linear","symbol":sym,"limit":1}, timeout=2)
        rate=0.0
        try:
            rate=float(fr.json().get("result",{}).get("list",[{"fundingRate":"0"}])[0]["fundingRate"])
        except Exception:
            rate=0.0
        mark=float(it.get("lastPrice") or 0.0)
        return {"venue":"BYBIT","rate_8h":rate,"mark":mark}

def best_funding(sym):
    best=None
    for v in VENUES:
        try:
            data = binance_funding(sym) if v=="BINANCE" else bybit_funding(sym)
            if best is None or abs(data["rate_8h"])>abs(best["rate_8h"]):
                best=data
        except Exception:
            continue
    return best or {"venue":"NONE","rate_8h":0.0,"mark":0.0}

def run():
    seen={}
    while True:
        now=int(time.time())
        if not ENABLE:
            time.sleep(10); continue
        for sym in SYMS:
            try:
                d=best_funding(sym)
                apr=apr_from_rate(d["rate_8h"])
                r.hset("funding:apr", sym, round(apr,4))
                if abs(apr) >= APR_MIN:
                    last=seen.get(sym,0)
                    if now-last<COOLDOWN_SEC:
                        continue
                    side = "SHORT_PERP_LONG_SPOT" if apr>0 else "LONG_PERP_SHORT_SPOT"
                    r.lpush(DQ_CEX, json.dumps({
                        "type":"CEX_FUNDING_ARBIT",
                        "symbol": sym,
                        "venue": d["venue"],
                        "apr": round(apr,4),
                        "side": side,
                        "ts": now,
                        "dry": not TRADE_ENABLE
                    }))
                    seen[sym]=now
            except Exception as e:
                r.hset("funding:error", sym, str(e))
        time.sleep(20)

if __name__=="__main__":
    run()

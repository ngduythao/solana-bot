
import os, time, math, redis
from cex_clients.binance_client import BINANCE_ENABLE, place_spot_order as bin_order
from cex_clients.bybit_client import BYBIT_ENABLE, place_spot_order as byb_order

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
HEDGE_INTERVAL_SEC=int(os.getenv("HEDGE_INTERVAL_SEC","300"))
INVENTORY_SKEW_CAP=float(os.getenv("INVENTORY_SKEW_CAP","0.1"))  # 10% NAV
MIN_NOTIONAL_USD=float(os.getenv("HEDGE_MIN_NOTIONAL_USD","25"))

# Basic symbol map (adjust as needed based on your exchange listings)
BINANCE_MAP={
  "SOL":"SOLUSDT","JUP":"JUPUSDT","BONK":"BONKUSDT","WIF":"WIFUSDT"
}
BYBIT_MAP={
  "SOL":"SOLUSDT","JUP":"JUPUSDT","BONK":"BONKUSDT","WIF":"WIFUSDT"
}

r=redis.from_url(REDIS_URL)

def get_nav()->float:
    try: return float(r.get("hb:nav:usd") or 0.0)
    except: return 0.0

def balances()->dict:
    # Expect balances pushed by accounting (token->amount); fallback zeros
    try:
        raw = r.hgetall("hb:balances")
        return { k.decode(): float(v.decode()) for k,v in raw.items() }
    except: return {}

def price_usd(token:str)->float:
    # Expect pricing in Redis (from Pyth/oracle feed dispatcher); fallback 0
    try: return float(r.hget("hb:price:usd", token) or 0.0)
    except: return 0.0

def need_hedge(token, amt)->float:
    nav=get_nav()
    if nav<=0: return 0.0
    usd=amt*price_usd(token)
    ratio = usd/max(nav,1e-9)
    if ratio>=INVENTORY_SKEW_CAP:
        return usd
    return 0.0

def place(symbol, side, qty, prefer="binance"):
    if prefer=="binance" and BINANCE_ENABLE:
        return bin_order(symbol, side, qty)
    if BYBIT_ENABLE:
        return byb_order(symbol, side, qty)
    # if only one enabled, try that
    if BINANCE_ENABLE:
        return bin_order(symbol, side, qty)
    return {"dry_run": True, "symbol":symbol, "side":side, "qty":qty}

def run():
    while True:
        try:
            bals = balances()  # e.g., {"USDC": 5000, "SOL":1.2, "JUP":1000, ...}
            for tk, amt in bals.items():
                if tk in ("USDC","USDT"): continue
                usd_need = need_hedge(tk, amt)
                if usd_need >= MIN_NOTIONAL_USD:
                    sym = BINANCE_MAP.get(tk) or BYBIT_MAP.get(tk)
                    if not sym: 
                        r.lpush("hedge:warn", f"no mapping for {tk}")
                        continue
                    # naive qty: sell full amount (market)
                    side="SELL"; qty=float(amt)
                    res = place(sym, side, qty, prefer="binance")
                    r.lpush("hedge:tx", str({"tk":tk,"sym":sym,"side":side,"qty":qty,"res":res}))
                    # set balance down (optimistic), real system should refresh from chain
                    r.hset("hb:balances", tk, 0.0)
        except Exception as e:
            r.lpush("hedge:err", str(e))
        time.sleep(HEDGE_INTERVAL_SEC)

if __name__=="__main__":
    run()

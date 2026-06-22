
import os, time, json, redis

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
SOL_MIN = float(os.getenv("SOL_MIN_RESERVE","0.8"))
BASE = (os.getenv("HEDGE_BASE","USDC") or "USDC").upper()
INTERVAL = int(os.getenv("HEDGE_INTERVAL_SEC","480"))
MIN_SWAP = float(os.getenv("MIN_SWAP_USD","10"))

TOKENS = ["USDC","SOL","JUP","BONK","WIF"]

def get_balances():
    out={}
    for t in TOKENS:
        try:
            out[t]=float(r.get(f"hsbot:bal:{t}") or 0.0)
        except: out[t]=0.0
    return out

def schedule_hedges():
    bals = get_balances()
    # 1) giữ USDC toàn bộ, SOL tối thiểu để trả phí
    sol = bals.get("SOL",0.0)
    if sol > SOL_MIN:
        amt = sol - SOL_MIN
        if amt* (r.get("hsbot:price:SOL") and float(r.get("hsbot:price:SOL")) or 150.0) >= MIN_SWAP:
            # Swap SOL dư -> USDC
            r.lpush("hsbot:hedge", json.dumps({"ts": time.time(), "size_usd": amt * float(r.get("hsbot:price:SOL") or 150.0), "to": "USDC"}))
    # 2) token lẻ (JUP/BONK/WIF) -> USDC
    for t in ["JUP","BONK","WIF"]:
        v = bals.get(t,0.0)
        px = float(r.get(f"hsbot:price:{t}") or 1.0)
        usd = v*px
        if usd >= MIN_SWAP:
            r.lpush("hsbot:hedge", json.dumps({"ts": time.time(), "size_usd": usd, "to": "USDC", "from": t}))

def main():
    print("[capital_manager] running (interval=", INTERVAL, "s)")
    nxt = 0
    while True:
        now = time.time()
        if now>=nxt:
            schedule_hedges()
            nxt = now + INTERVAL
        time.sleep(2)

if __name__=="__main__":
    main()

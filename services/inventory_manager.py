
import os, time, json, httpx, math
import redis

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
RPC = os.getenv("RPC_PRIMARY","https://api.mainnet-beta.solana.com")
JUP = os.getenv("JUP_BASE","https://quote-api.jup.ag")
BASE = os.getenv("HEDGE_BASE","USDC")
THRESH_BPS = int(os.getenv("HEDGE_THRESH_BPS","800"))
MIN_USD = float(os.getenv("HEDGE_MIN_USD","200"))
MAX_DEPTH = float(os.getenv("MAX_DEPTH_PCT_PER_LEG","0.15"))

MINTS = {
  "SOL": "So11111111111111111111111111111111111111112",
  "USDC":"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "JUP":"JUP2jxvGmG2h3zWZ1j5qS9gGZ7wS9Vt7d1b7W5HYi",
  "BONK":"DezXAZ8z7Pnrn974i1qAqE9v6zE2fqBeH5bC7Z7x8Px",
  "WIF":"WifQ1RZ1xWifxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}

def get_nav_usd():
    try:
        return float(r.get("hsbot:cfg:nav_usd") or 10000.0)
    except: return 10000.0

def get_balances():
    # Expect executor/orchestrator to update balances per token in Redis.
    # Fallback demo values:
    out = {}
    for t in ["USDC","SOL","JUP","BONK","WIF"]:
        out[t] = float(r.get(f"hsbot:bal:{t}") or 0.0)
    return out

def maybe_hedge():
    nav = get_nav_usd()
    bals = get_balances()
    base = BASE
    non_base_usd = 0.0
    # assume price 1 for USDC; others need price from Pyth in prod; here we simplify using route quote when executing.
    for t,v in bals.items():
        if t==base or v<=0: continue
        # push a hedge instruction into a queue for executor to route via Jupiter with size capped by depth later
        # simple rule: if sum non-base > THRESH% NAV => hedge down to threshold
        non_base_usd += v  # assume 1 USD per unit for simplification; in prod fetch pyth price
    if non_base_usd/nav*1e4 > THRESH_BPS and non_base_usd > MIN_USD:
        size = max(MIN_USD, non_base_usd - nav*THRESH_BPS/1e4)
        r.lpush("hsbot:hedge", json.dumps({"ts": time.time(), "size_usd": round(size,2), "to": base}))
        r.publish("hsbot:alerts", json.dumps({"type":"hedge", "size_usd": size, "to": base}))

def main():
    while True:
        if os.getenv("HEDGE_ENABLE","1")=="1":
            maybe_hedge()
        time.sleep(10)

if __name__=="__main__":
    print("[inventory_manager] running")
    main()

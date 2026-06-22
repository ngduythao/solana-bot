
import os, time, json, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

ALLOWED_MINTS=set((os.getenv("JUP_ALLOWED_MINTS","USDC,SOL")).split(","))
MAX_SLIPPAGE_BPS=int(os.getenv("JUP_MAX_SLIPPAGE_BPS","80"))
SWAP_RATE_LIMIT=int(os.getenv("JUP_RATE_LIMIT_PER_MIN","20"))
DAILY_USDC_CAP=float(os.getenv("JUP_DAILY_USDC_CAP","5000"))
ARM_KEY="solbot:jup:armed"      # require arm before HOT swaps (2‑step arming)
USDC_DECIMALS=int(os.getenv("USDC_DECIMALS","6"))

def now_minute(): return int(time.time()//60)

def check_armed():
    v=r.get(ARM_KEY)
    return v and v.decode()=="1"

def set_armed(seconds=600):
    r.setex(ARM_KEY, seconds, "1")

def minute_key(m): return f"solbot:jup:min:{m}:count"
def daily_key(d):  return f"solbot:jup:day:{d}:usdc"

def today(): 
    import datetime as dt
    return dt.date.today().isoformat()

def can_swap(usdc_equiv, want_mints):
    # allowlist
    for m in want_mints:
        if m not in ALLOWED_MINTS:
            return False, "mint_not_allowed"
    # arming
    if os.getenv("SIGNER_MODE","paper").lower()=="hot" and not check_armed():
        return False, "not_armed"
    # rate limit per minute
    k=minute_key(now_minute())
    c=int(r.get(k) or 0)
    if c>=SWAP_RATE_LIMIT:
        return False, "rate_limited"
    # daily cap
    kd=daily_key(today())
    used=float(r.get(kd) or 0.0)
    if used + usdc_equiv > DAILY_USDC_CAP:
        return False, "daily_cap_exceeded"
    return True, ""

def account(usdc_equiv):
    # increment counters
    k=minute_key(now_minute()); r.incr(k); r.expire(k, 120)
    kd=daily_key(today()); r.incrbyfloat(kd, float(usdc_equiv)); r.expire(kd, 86400*2)

def bps_ok(bps):
    return bps<=MAX_SLIPPAGE_BPS

def usdc_equiv_from_sol(sol_price, amount_sol):
    # if no price, rough proxy 1 SOL~100 USDC (can be overridden via env)
    p=float(os.getenv("SOL_USDC_PRICE_HINT","100"))
    try:
        sp=float(sol_price) if sol_price else p
    except: sp=p
    return float(amount_sol)*sp

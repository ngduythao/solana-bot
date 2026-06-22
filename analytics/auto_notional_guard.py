
import os, csv, time, math, json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
METRICS_PATH = os.getenv("METRICS_PATH","metrics.csv")

ENABLE = int(os.getenv("NOTIONAL_GUARD_ENABLE","1"))
WINDOW_SEC = int(os.getenv("NOTIONAL_GUARD_WINDOW_SEC","900"))  # 15m
P95_BAD = float(os.getenv("NOTIONAL_GUARD_P95_BAD_MS","150"))
P95_GOOD = float(os.getenv("NOTIONAL_GUARD_P95_GOOD_MS","100"))
STEP_DOWN = float(os.getenv("NOTIONAL_GUARD_STEP_DOWN","0.8"))
STEP_UP = float(os.getenv("NOTIONAL_GUARD_STEP_UP","1.05"))
MULT_MIN = float(os.getenv("NOTIONAL_GUARD_MULT_MIN","0.3"))
MULT_MAX = float(os.getenv("NOTIONAL_GUARD_MULT_MAX","1.0"))
TTL = int(os.getenv("NOTIONAL_GUARD_TTL_SEC","300"))

BASE_MIN_NOTIONAL = float(os.getenv("GUARD_BASE_MIN_NOTIONAL_USD","25"))
BASE_PER_MINT = os.getenv("GUARD_BASE_PER_MINT_LIMIT_USD_MAP","SOL:2000,JUP:1500,WIF:800,BONK:1000")

SLEEP = int(os.getenv("NOTIONAL_GUARD_POLL_SEC","10"))

def p95(vals):
    if not vals: return 0.0
    s=sorted(vals)
    k=int(math.ceil(0.95*len(s)))-1
    return float(s[max(0,min(k,len(s)-1))])

def parse_tail(path, window):
    try:
        with open(path,'r',encoding='utf-8') as f:
            rows=list(csv.DictReader(f))
    except FileNotFoundError:
        return []
    now=time.time()
    out=[]
    for r in rows[-5000:]:
        try:
            ts=float(r.get("ts",now))
            if now - ts > window: continue
            lat=float(r.get("latency_ms", r.get("lat_ms", 0)) or 0)
            out.append(lat)
        except: pass
    return out

def parse_per_mint_map(s):
    out={}
    for kv in s.split(","):
        kv=kv.strip()
        if not kv: continue
        mint,val=kv.split(":")
        out[mint.upper()]=float(val)
    return out

def main():
    if not ENABLE:
        return
    r=redis.from_url(REDIS_URL)
    mult_key="hsbot:notional:mult"
    # init mult if missing
    if not r.get(mult_key):
        r.set(mult_key, str(MULT_MAX))

    base_per_mint = parse_per_mint_map(BASE_PER_MINT)
    while True:
        lats = parse_tail(METRICS_PATH, WINDOW_SEC)
        p = p95(lats)
        try:
            mult=float(r.get(mult_key) or MULT_MAX)
        except Exception:
            mult=MULT_MAX

        if p >= P95_BAD:
            mult = max(MULT_MIN, mult*STEP_DOWN)
        elif p>0 and p <= P95_GOOD:
            mult = min(MULT_MAX, mult*STEP_UP)

        r.set(mult_key, f"{mult:.4f}")
        # write Redis overrides for hedger sizing
        new_min = max(1.0, BASE_MIN_NOTIONAL*mult)
        r.setex("hsbot:hedge:cfg:min_notional_usd:default", TTL, f"{new_min:.2f}")
        for mint,limit in base_per_mint.items():
            r.setex(f"hsbot:hedge:cfg:per_mint_limit_usd:{mint}", TTL, f"{limit*mult:.2f}")

        r.setex("hsbot:notional:last_p95", TTL, f"{p:.2f}")
        r.setex("hsbot:notional:mult_effective", TTL, f"{mult:.2f}")
        time.sleep(SLEEP)

if __name__ == "__main__":
    main()

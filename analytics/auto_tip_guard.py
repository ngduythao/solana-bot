
import os, csv, time, math, json
import redis

# Inputs & knobs
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
METRICS_PATH = os.getenv("METRICS_PATH","metrics.csv")

ENABLE = int(os.getenv("TIP_GUARD_ENABLE","1"))
WINDOW_SEC = int(os.getenv("TIP_GUARD_WINDOW_SEC","900"))  # 15m
P95_SLOW = float(os.getenv("TIP_GUARD_P95_SLOW_MS","130"))
P95_FAST = float(os.getenv("TIP_GUARD_P95_FAST_MS","90"))
FILL_BAD = float(os.getenv("TIP_GUARD_FILL_BAD","0.42"))
FILL_GOOD = float(os.getenv("TIP_GUARD_FILL_GOOD","0.58"))

STEP_UP = float(os.getenv("TIP_GUARD_STEP_UP","1.05"))
STEP_DOWN = float(os.getenv("TIP_GUARD_STEP_DOWN","0.97"))
MULT_MIN = float(os.getenv("TIP_GUARD_MULT_MIN","0.45"))
MULT_MAX = float(os.getenv("TIP_GUARD_MULT_MAX","0.9"))
TTL = int(os.getenv("TIP_GUARD_TTL_SEC","300"))

DEFAULT_MINTS = os.getenv("TIP_GUARD_MINTS","SOL,JUP,WIF,BONK").split(",")

def p95(vals):
    if not vals: return 0.0
    s=sorted(vals)
    k=int(math.ceil(0.95*len(s)))-1
    return float(s[max(0,min(k,len(s)-1))])

def tail_metrics(path, window):
    try:
        with open(path,'r',encoding='utf-8') as f:
            rows=list(csv.DictReader(f))
    except FileNotFoundError:
        return [],0.0,0.0
    now=time.time()
    lats=[]; wins=0; cnt=0
    for r in rows[-5000:]:
        try:
            ts=float(r.get("ts",now))
            if now - ts > window: continue
            lat=float(r.get("latency_ms", r.get("lat_ms", 0)) or 0)
            pnl=float(r.get("pnl_usd", r.get("pnl", 0)) or 0)
            lats.append(lat)
            cnt += 1
            if pnl>0: wins += 1
        except: pass
    wr = (wins/cnt) if cnt>0 else 0.0
    return lats, p95(lats), wr

def main():
    if not ENABLE: return
    r=redis.from_url(REDIS_URL)
    mult_key="hsbot:tip:mult"
    if not r.get(mult_key):
        r.set(mult_key, str(MULT_MIN))

    while True:
        lats, p95lat, wr = tail_metrics(METRICS_PATH, WINDOW_SEC)
        try:
            mult=float(r.get(mult_key) or MULT_MIN)
        except Exception:
            mult=MULT_MIN

        # Logic: if latency slow or fill-rate bad -> increase tip (mult up)
        if (p95lat>=P95_SLOW) or (wr>0 and wr<=FILL_BAD):
            mult=min(MULT_MAX, mult*STEP_UP)
        elif (p95lat>0 and p95lat<=P95_FAST) and (wr>=FILL_GOOD):
            mult=max(MULT_MIN, mult*STEP_DOWN)

        r.setex(mult_key, TTL, f"{mult:.4f}")
        # write per-mint tip multiplier overrides
        for mint in DEFAULT_MINTS:
            mint=mint.strip().upper()
            if not mint: continue
            r.setex(f"hsbot:hedge:cfg:prio_mult:{mint}", TTL, f"{mult:.4f}")
        r.setex("hsbot:tip:last_p95", TTL, f"{p95lat:.2f}")
        r.setex("hsbot:tip:last_wr", TTL, f"{wr:.4f}")
        r.setex("hsbot:tip:mult_effective", TTL, f"{mult:.4f}")
        time.sleep(10)

if __name__ == "__main__":
    main()

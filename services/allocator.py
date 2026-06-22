
import os, time, json, redis

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
DECAY = float(os.getenv("ALLOC_DECAY","0.95"))
MIN_BPS = float(os.getenv("ALLOC_MIN_BPS","5"))

PAIRS = ["SOL/USDC","JUP/USDC","BONK/USDC","WIF/USDC"]

def step():
    scores = {}
    total = 0.0
    for p in PAIRS:
        pnlps = float(r.get(f"hsbot:pnlps:{p}") or 0.0)
        pnlps *= DECAY
        r.set(f"hsbot:pnlps:{p}", pnlps)
        scores[p] = max(0.0, pnlps)
        total += scores[p]
    weights = {}
    if total==0.0:
        # equal split minimal bps
        for p in PAIRS:
            weights[p] = MIN_BPS
    else:
        for p in PAIRS:
            w = (scores[p]/total)* (10000 - MIN_BPS*len(PAIRS)) + MIN_BPS
            weights[p]= w
    r.set("hsbot:alloc_weights", json.dumps(weights))

def loop():
    print("[allocator] running")
    while True:
        step()
        time.sleep(5)

if __name__=="__main__":
    loop()

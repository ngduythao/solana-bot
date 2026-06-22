#!/usr/bin/env python3
import time, os
try:
    import redis
    r=redis.Redis(host="localhost", port=6379, decode_responses=True)
except Exception:
    r=None

PAIRS = ["SOL/USDC","JUP/USDC","WIF/USDC","BONK/USDC"]

def get(k, default=None):
    if not r: return default
    try: v=r.get(k); return v if v is not None else default
    except Exception: return default

def setk(k,v):
    if not r: return
    try: r.set(k,str(v))
    except Exception: pass

def loop():
    base_mult = float(get("hsbot:notional:mult_base","1.0") or 1.0)
    for p in PAIRS:
        cap = float(get(f"hsbot:cap:{p}","0.25") or 0.25)
        eff = max(0.05, min(1.0, base_mult * cap))
        setk(f"hsbot:notional:mult_effective:{p}", eff)

if __name__=="__main__":
    while True:
        try: loop()
        except Exception: pass
        time.sleep(5)

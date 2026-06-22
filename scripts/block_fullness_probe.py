#!/usr/bin/env python3
import time, os, statistics
try:
    import redis
    r=redis.Redis(host='localhost', port=6379, decode_responses=True)
except Exception:
    r=None

def getf(k, d=0.0):
    try:
        v = r.get(k)
        return float(v) if v is not None else d
    except Exception:
        return d

def setk(k,v):
    try:
        r.set(k, str(v))
    except Exception:
        pass

def loop():
    while True:
        lat95 = getf("hsbot:lat_p95", 40.0)
        rtt95 = getf("jito:rtt_p95", 120.0)
        fullness = min(100.0, max(5.0, 0.4*lat95 + 0.6*min(300.0,rtt95)))
        mult = round(0.8 + (fullness/100.0)*1.2, 2)
        setk("hsbot:block_fullness", round(fullness,2))
        setk("hsbot:jito:tip_mult", mult)
        time.sleep(10)

if __name__=="__main__":
    loop()

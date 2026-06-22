#!/usr/bin/env python3
import time
try:
    import redis
    r=redis.Redis(host='localhost', port=6379, decode_responses=True)
except Exception:
    r=None

def getf(k,d):
    try:
        v=r.get(k)
        return float(v) if v is not None else d
    except Exception:
        return d

def loop():
    # token bucket redis keys
    # hsbot:pacer:qps, hsbot:pacer:tokens, hsbot:pacer:burst
    while True:
        fullness = getf("hsbot:block_fullness", 40.0)  # 0..100
        # Map fullness to qps (low fullness => higher qps)
        qps = max(0.5, 6.0 - 0.05*fullness)  # 6 qps at 0 fullness -> 1 qps at 100
        burst = 10
        try:
            r.set("hsbot:pacer:qps", round(qps,2))
            r.set("hsbot:pacer:burst", burst)
            # refill tokens
            now = time.time()
            # use a simple per-second refill
            r.incrbyfloat("hsbot:pacer:tokens", qps/2.0)
            # clamp
            tok = float(r.get("hsbot:pacer:tokens") or 0.0)
            if tok>burst: r.set("hsbot:pacer:tokens", burst)
        except Exception:
            pass
        time.sleep(0.5)

if __name__=="__main__":
    loop()

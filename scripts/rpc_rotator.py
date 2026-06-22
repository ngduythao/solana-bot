#!/usr/bin/env python3
import os, time, statistics, json, subprocess, re
try:
    import redis
    r=redis.Redis(host='localhost', port=6379, decode_responses=True)
except Exception:
    r=None

CANDS = os.environ.get("RPC_CANDIDATES","").split(",")
CANDS = [c.strip() for c in CANDS if c.strip()]

def probe_once(url:str):
    # Use curl time + simple /health path if exists; fall back to TCP connect via curl
    try:
        out = subprocess.check_output(["bash","-lc", f"(time -p curl -m 1 -s -o /dev/null '{url}') 2>&1 | awk '/real/{{print $2*1000}}'"], text=True, timeout=2)
        ms  = float(out.strip() or "999")
        err = 0.0 if ms < 900 else 1.0
        return ms, err
    except Exception:
        return 999.0, 1.0

def loop():
    hist = {c: [] for c in CANDS}
    while True:
        for c in CANDS:
            ms, e = probe_once(c)
            try:
                r.lpush(f"rpc:hist:{c}", ms); r.ltrim(f"rpc:hist:{c}", 0, 59)
                r.lpush(f"rpc:err:{c}", e);  r.ltrim(f"rpc:err:{c}", 0, 59)
                arr = list(map(float, r.lrange(f"rpc:hist:{c}",0,59)))
                p95 = sorted(arr)[int(0.95*len(arr))-1] if arr else 999.0
                er  = sum(map(float, r.lrange(f"rpc:err:{c}",0,59))) / max(1,len(arr))
                r.set(f"rpc:latency:p95:{c}", round(p95,2))
                r.set(f"rpc:error_rate:{c}", round(er,3))
            except Exception:
                pass
        # choose best
        best = None; best_score = 1e9
        for c in CANDS:
            try:
                p95 = float(r.get(f"rpc:latency:p95:{c}") or 999.0)
                er  = float(r.get(f"rpc:error_rate:{c}") or 1.0)
                score = 0.8*p95 + 2000*er  # weight: 0.8ms + penalty for errors
                if score < best_score:
                    best_score, best = score, c
            except Exception:
                continue
        if best:
            r.set("rpc:current", best)
        time.sleep(5)

if __name__=='__main__':
    loop()


# --- alert on spike & keep ws:current in sync ---
import os as _os
def _notify(msg):
    try:
        _os.system(f"./scripts/tg_notify.sh \"{msg}\" >/dev/null 2>&1")
    except Exception:
        pass

def _derive_ws(url:str)->str:
    from urllib.parse import urlparse
    u=urlparse(url)
    sch='wss' if u.scheme in('https','wss') else 'ws'
    net=u.netloc or u.path
    return f"{sch}://{net}"

prev_best=None
while True:
    # (existing loop already sets best)
    break

def watch_loop():
    import time
    last = r.get("rpc:current")
    while True:
        cur = r.get("rpc:current")
        if cur and cur != last:
            p95 = r.get(f"rpc:latency:p95:{cur}") or "n/a"
            er  = r.get(f"rpc:error_rate:{cur}") or "n/a"
            _notify(f"🔄 RPC switched → {cur} (p95={p95}ms, err={er})")
            # sync ws
            r.set("ws:current", _derive_ws(cur))
            last = cur
        # alert when current rpc error rate spikes
        if cur:
            try:
                erc=float(r.get(f"rpc:error_rate:{cur}") or 0.0)
                if erc>0.25:
                    _notify(f"⚠️ RPC error spike on {cur}: {erc*100:.0f}%")
            except Exception:
                pass
        time.sleep(3)
if __name__=='__main__':
    try:
        watch_loop()
    except KeyboardInterrupt:
        pass

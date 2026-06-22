
import os, time, json, httpx, redis, statistics
from datetime import datetime

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

def targets_from_env():
    t=[]
    def add(name, url):
        if url: t.append((name, url))
    add("primary", os.getenv("RPC_PRIMARY"))
    for i in range(1,6):
        add(f"fallback_{i}", os.getenv(f"RPC_FALLBACK_{i}"))
    return [(n,u) for (n,u) in t if u]

def ping(url, n=5, timeout=1.8):
    lat=[]
    body={"jsonrpc":"2.0","id":1,"method":"getLatestBlockhash","params":[{"commitment":"confirmed"}]}
    with httpx.Client(http2=True) as c:
        for _ in range(n):
            t0=time.perf_counter()
            try:
                res=c.post(url, json=body, timeout=timeout)
                ok = res.status_code==200 and res.json().get("result") is not None
            except Exception:
                ok=False
            dt=(time.perf_counter()-t0)*1000.0
            if ok: lat.append(dt)
            time.sleep(0.1)
    if not lat: return None
    p95=statistics.quantiles(lat, n=20)[-1] if len(lat)>=5 else max(lat)
    return {"count": len(lat), "p50": statistics.median(lat), "p95": p95, "avg": sum(lat)/len(lat)}

def run_once():
    tg=targets_from_env()
    best=None
    best_p95=1e9
    results={}
    for name,url in tg:
        r.hset('rpc:url', name, url or '')
        m=ping(url)
        if m is None:
            continue
        results[name]=m
        r.hset("rpc:latency:p95", name, round(m["p95"],2))
        if m["p95"]<best_p95:
            best_p95=m["p95"]; best=name
    if best:
        r.set("rpc:best", best)
        r.set("rpc:best_p95", round(best_p95,2))
        r.set("rpc:last_bench_ts", int(time.time()))
    r.set("rpc:last_results", json.dumps(results))

if __name__=="__main__":
    interval=int(os.getenv("RPC_BENCH_INTERVAL_SEC","300"))
    while True:
        run_once()
        time.sleep(interval)

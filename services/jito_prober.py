
#!/usr/bin/env python3
import os, time, math, json, asyncio, statistics as st
import redis
try:
    import websockets
except Exception:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
RELAYS=[s.strip() for s in os.getenv("JITO_RELAYS_CANDIDATES","").split(",") if s.strip()]
TTL=int(os.getenv("PROBER_TTL_SEC","120"))
INTERVAL=float(os.getenv("PROBER_INTERVAL_SEC","5"))
SAMPLES=int(os.getenv("PROBER_SAMPLES","5"))

r=redis.from_url(REDIS_URL)

async def ping_once(url, timeout=2.0):
    t0=time.time()
    try:
        async with websockets.connect(url, ping_interval=None, close_timeout=1) as ws:
            await ws.ping()
            await asyncio.wait_for(ws.recv(), timeout=timeout)  # likely no reply, will timeout
            # If recv returns something quickly, it's fine; measure elapsed
    except Exception:
        pass
    return (time.time()-t0)*1000.0

async def measure(url):
    vals=[]
    for _ in range(SAMPLES):
        try:
            v=await ping_once(url)
            vals.append(v)
        except Exception:
            vals.append(9999.0)
    p50=st.median(vals)
    vals_sorted=sorted(vals); k=max(0,min(len(vals_sorted)-1,int(math.ceil(0.95*len(vals_sorted)))-1))
    p95=vals_sorted[k]
    return p50,p95

async def main():
    while True:
        results={}
        for url in RELAYS:
            try:
                p50,p95=await measure(url)
                keybase=f"jito:rtt:{url}"
                r.setex(keybase+":p50",TTL,f"{p50:.2f}")
                r.setex(keybase+":p95",TTL,f"{p95:.2f}")
                results[url]={"p50":p50,"p95":p95}
            except Exception as e:
                r.setex(f"jito:rtt:{url}:p50",TTL,"9999")
                r.setex(f"jito:rtt:{url}:p95",TTL,"9999")
        # choose best relay (by p50)
        if results:
            best=min(results.items(), key=lambda kv: kv[1]["p50"])
            r.setex("jito:rtt:best_url",TTL,best[0])
            r.setex("jito:rtt:best_p95",TTL,f"{best[1]['p95']:.2f}")
        time.sleep(INTERVAL)

if __name__=="__main__":
    asyncio.run(main())

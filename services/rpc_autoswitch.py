
import os, time, json, httpx, redis

REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
r = redis.from_url(REDIS_URL)

PRIMARY = os.getenv("RPC_PRIMARY") or os.getenv("HELIUS_RPC") or "https://api.mainnet-beta.solana.com"
FALLBACKS = [x.strip() for x in (os.getenv("RPC_FALLBACKS","").split(",") if os.getenv("RPC_FALLBACKS") else []) if x.strip()]

WIN = int(os.getenv("RPC_ERR_WINDOW_SEC","300"))
CAP = float(os.getenv("RPC_ERR_RATE_CAP_PCT","20"))
COOLDOWN = int(os.getenv("RPC_SWITCH_COOLDOWN_SEC","600"))

def rpc_list():
    cur = r.get("hsbot:cfg:rpc_primary")
    cur = cur.decode() if cur else PRIMARY
    out = [cur] + [x for x in FALLBACKS if x!=cur]
    return out

def probe(url):
    # record latency EWM to Redis for dashboard
    try:
        with httpx.Client(timeout=2.5) as c:
            t0 = time.time()
            resp = c.post(url, json={"jsonrpc":"2.0","id":1,"method":"getHealth"})
            latency = (time.time()-t0)*1000.0
            ok = resp.status_code==200 and 'ok' in resp.text.lower()
                        # Update EMA latency and ok/err counters for dashboard
            key = f"hsbot:rpc:lat_ms:{url}"
            prev = float(r.get(key) or 0.0)
            ema = (prev*0.8 + latency*0.2) if prev>0 else latency
            r.set(key, round(ema,2))
            r.incr(f"hsbot:rpc:ok:{url}" if ok else f"hsbot:rpc:err:{url}")
            return ok, latency
    except Exception:
        return False, 10_000.0

def window_err_rate(url):
    # Expect other services to increment hsbot:rpc:ok:<url> / hsbot:rpc:err:<url>
    ok = int(r.get(f"hsbot:rpc:ok:{url}") or 0)
    err = int(r.get(f"hsbot:rpc:err:{url}") or 0)
    tot = ok+err
    return (err/max(1,tot))*100.0

def main():
    last_switch = 0
    # initialize primary if not set
    if not r.get("hsbot:cfg:rpc_primary"):
        r.set("hsbot:cfg:rpc_primary", PRIMARY)
    while True:
        best = None
        best_lat = 1e9
        url_err = {}
        for url in rpc_list():
            ok, lat = probe(url)
            if ok and lat < best_lat:
                best, best_lat = url, lat
            # rough error rate
            er = window_err_rate(url)
            url_err[url] = er
        cur = (r.get("hsbot:cfg:rpc_primary") or PRIMARY.encode()).decode()
        cur_er = url_err.get(cur, 0.0)
        # switch if current is bad and another is healthy & faster
        if (cur_er > CAP or best_lat < 500 and best!=cur) and (time.time()-last_switch>COOLDOWN):
            r.set("hsbot:cfg:rpc_primary", best or PRIMARY)
            r.publish("hsbot:alerts", json.dumps({"type":"rpc_switch","from":cur,"to":best,"cur_err":cur_er,"lat_ms":best_lat}))
            last_switch = time.time()
        time.sleep(5)

if __name__=="__main__":
    main()

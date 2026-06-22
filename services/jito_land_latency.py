
import os, time, json, redis
# NOTE: This is a scaffold. Provide Jito WS/stream; push events as {"relay": "...", "accepted_ts":..., "landed_ts":...}
# We'll compute latency and feed slo aggregator / tipcurve automatically.
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
KEY="solbot:jito:events"

def main():
    print("[jito_land_latency] scaffold running")
    while True:
        try:
            it=r.rpop(KEY)
            if not it:
                time.sleep(1); continue
            ev=json.loads(it)
            relay=ev.get("relay","rel_unknown")
            lat_ms=max(0, int(1000*(ev.get("landed_ts",0)-ev.get("accepted_ts",0))))
            rec={"relay": relay, "lat_ms": lat_ms, "ts": time.time()}
            r.lpush("solbot:fast_res", json.dumps(rec)); r.ltrim("solbot:fast_res",0,2000)
        except Exception: pass

if __name__=="__main__":
    main()


import os, time, json, redis, statistics
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def main():
    print("[relay_landlat] running")
    while True:
        try:
            arr=r.lrange("solbot:tx_land",0,500)
            buckets={}
            for it in arr:
                try:
                    j=json.loads(it)
                except: continue
                rel=j.get("relay"); lat=j.get("land_ms"); ts=j.get("ts")
                if not rel or not lat: continue
                buckets.setdefault(rel,[]).append(float(lat))
            for rel, vals in buckets.items():
                if vals:
                    vals.sort()
                    p50=vals[len(vals)//2]; p95=vals[int(len(vals)*0.95)-1] if len(vals)>=20 else max(vals)
                    r.setex(f"slo:{rel}:land:p50",60,str(p50))
                    r.setex(f"slo:{rel}:land:p95",60,str(p95))
        except: pass
        time.sleep(5)
if __name__=="__main__":
    main()

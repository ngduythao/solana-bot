
import os, time, json, redis, statistics, datetime as dt
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

WINDOW=int(os.getenv("SLO_WINDOW","1200"))  # how many recent samples to consider
RELAYS=os.getenv("RELAYS_CANDIDATES","relay_sg_1,relay_sg_2,relay_nj_1,relay_nj_2").split(",")

def median(xs):
    try: return statistics.median(xs) if xs else 0.0
    except: return 0.0

def main():
    print("[relay_slo_agg] running")
    while True:
        try:
            # Expect samples in list 'solbot:fast_res' with JSON {"relay": "...", "lat_ms": 123, "ts": ...}
            buckets={}  # {(relay,hour): [lat...]}
            arr=r.lrange("solbot:fast_res", 0, WINDOW)
            now=dt.datetime.utcnow()
            for it in arr:
                try:
                    j=json.loads(it)
                except Exception:
                    continue
                rel=j.get("relay"); lat=float(j.get("lat_ms",0)); ts=float(j.get("ts", time.time()))
                if not rel or lat<=0: continue
                h=dt.datetime.utcfromtimestamp(ts).hour
                key=(rel, h)
                buckets.setdefault(key, []).append(lat)
            # Write aggregates into keys slo:<relay>:<hour>:p50/p95 used by tipcurve builder
            for rel in RELAYS:
                for h in range(24):
                    lat_list=buckets.get((rel,h), [])
                    if lat_list:
                        lat_list.sort()
                        p50=lat_list[len(lat_list)//2]
                        p95=lat_list[int(len(lat_list)*0.95)-1] if len(lat_list)>=20 else max(lat_list)
                        r.setex(f"slo:{rel}:{h}:p50", 120, str(p50))
                        r.setex(f"slo:{rel}:{h}:p95", 120, str(p95))
        except Exception:
            pass
        time.sleep(5)

if __name__=="__main__":
    main()

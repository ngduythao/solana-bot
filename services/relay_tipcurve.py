
import os, time, json, redis, statistics, datetime as dt
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
RELAYS=os.getenv("RELAYS_CANDIDATES","relay_sg_1,relay_sg_2,relay_nj_1,relay_nj_2").split(",")
HOURS=list(range(24))

def main():
    print("[relay_tipcurve] running")
    while True:
        try:
            # gather recent latency per relay from slo stats (placeholder store under jito:relay_stats:<relay>)
            curve={}
            for rel in RELAYS:
                by_hour={}
                for h in HOURS:
                    # emulate reading p50/p95 from aggregated keys; fall back to rolling samples if present
                    p50=float(r.get(f"slo:{rel}:{h}:p50") or 900)
                    p95=float(r.get(f"slo:{rel}:{h}:p95") or 1400)
                    # simple baseline tip: higher when p95 is high
                    base = max(10000, int(15000 + (p95-1000)*20))
                    by_hour[str(h)] = {"p50": p50, "p95": p95, "tip_base": base}
                curve[rel]=by_hour
            r.setex("solbot:relay_tipcurve", 60, json.dumps(curve))
        except Exception: pass
        time.sleep(10)

if __name__=="__main__":
    main()

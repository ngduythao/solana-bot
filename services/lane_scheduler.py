
import os, time, json, redis, statistics
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
KEY="solbot:lane_schedule"

def score(acc, p50, p95):
    return (acc or 0) * 1000.0 - (p95 or 0)  # simple: favor accept%, penalize tail

def main():
    print("[lane_scheduler] running")
    while True:
        try:
            hour = int(time.time()//3600)%24
            table={}  # relay -> score
            for k in r.scan_iter(match="jito:relay_stats:*"):
                kd=k.decode()
                if kd.endswith(":leaders"): continue
                h=r.hgetall(k)
                try:
                    cnt=int(h.get(b'count',b'0') or 0); suc=int(h.get(b'success',b'0') or 0)
                    p50=float(h.get(b'p50_ms',b'0') or 0); p95=float(h.get(b'p95_ms',b'0') or 0)
                    acc=(suc/cnt) if cnt>0 else 0.0
                    table[kd]=score(acc,p50,p95)
                except: pass
            sched = json.loads(r.get(KEY) or b'{}')
            row = sched.get(str(hour), {})
            for rel, sc in table.items():
                # exponential moving max-like preference
                prev = row.get(rel, sc)
                row[rel] = 0.8*prev + 0.2*sc
            sched[str(hour)] = row
            r.set(KEY, json.dumps(sched))
        except Exception: pass
        time.sleep(60)

if __name__ == "__main__":
    main()

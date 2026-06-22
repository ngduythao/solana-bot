
import os, redis, time, csv, statistics
from datetime import datetime

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))

def percentiles(vals):
    if not vals: return None, None
    p50 = statistics.median(vals)
    vals = sorted(vals); p95 = vals[max(0, int(0.95*len(vals))-1)]
    return p50, p95

def main():
    rows=[]
    store = [float(x) for x in r.lrange("hsbot:lat_store", 0, 5000)]
    if not store:
        print("No latency data yet."); return
    # bucket by hour (naive: most recent window only)
    p50, p95 = percentiles(store)
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    rows.append({"ts": now, "p50_ms": round(p50,2), "p95_ms": round(p95,2)})
    os.makedirs("reports", exist_ok=True)
    with open("reports/latency_hourly.csv","a",newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ts","p50_ms","p95_ms"])
        if f.tell()==0: w.writeheader()
        w.writerows(rows)
    print("Wrote reports/latency_hourly.csv")

if __name__=="__main__":
    main()

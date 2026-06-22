
import os, time, json, statistics, redis

WIN_S = int(os.getenv("LAT_WINDOW_S","3600"))
TARGET = int(os.getenv("LAT_TARGET_P95_MS","100"))
r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))

def compute_percentiles(vals):
    if not vals: return None, None
    p50 = statistics.median(vals)
    vals_sorted = sorted(vals)
    idx = max(0, int(0.95*len(vals_sorted))-1)
    p95 = vals_sorted[idx]
    return p50, p95

def loop():
    while True:
        now = time.time()
        # Expect pipeline to push stage events with ts_detect, ts_sim, ts_submit into Redis list "hsbot:lat_events"
        rows = []
        for _ in range(512):
            blob = r.rpop("hsbot:lat_events")
            if not blob: break
            ev = json.loads(blob)
            if "ts_detect" in ev and "ts_submit" in ev:
                lat_ms = (ev["ts_submit"] - ev["ts_detect"])*1000.0
                rows.append(lat_ms)
        if rows:
            # keep rolling metrics
            for v in rows:
                r.lpush("hsbot:lat_store", v)
            r.ltrim("hsbot:lat_store", 0, 5000)
        store = r.lrange("hsbot:lat_store", 0, 5000)
        vals = [float(x) for x in store]
        p50, p95 = compute_percentiles(vals) if vals else (None,None)
        if p95 is not None:
            r.set("hsbot:lat:p50", p50); r.set("hsbot:lat:p95", p95)
            if p95 > TARGET:
                r.publish("hsbot:alerts", json.dumps({"type":"latency", "p95_ms": p95}))
        time.sleep(2)

if __name__=="__main__":
    print("[latency_meter] running")
    loop()

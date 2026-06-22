
import os, csv, time, redis
METRICS_PATH = os.getenv("METRICS_PATH","metrics.csv")
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def tail_metrics(n=5000):
    try:
        with open(METRICS_PATH,"r") as f:
            import csv as _csv
            rd = _csv.DictReader(f)
            rows = list(rd)[-n:]
        return rows
    except Exception:
        return []
def main():
    while True:
        rows = tail_metrics()
        p95s = [float(x.get("latency_ms",0))/1000.0 for x in rows if x.get("kind")=="jito_rtt_p95"]
        p95 = p95s[-1] if p95s else None
        if p95:
            base = max(5000, min(300000, int(p95*1e6*0.02)))
            tip_min = max(5000, int(base*0.5))
            tip_max = min(300000, int(base*2.0))
            step = max(1000, int((tip_max - tip_min)/20))
            r.set("hsbot:cfg:jito_tip_min", tip_min)
            r.set("hsbot:cfg:jito_tip_max", tip_max)
            r.set("hsbot:cfg:jito_tip_step", step)
        time.sleep(3)
if __name__=="__main__":
    main()

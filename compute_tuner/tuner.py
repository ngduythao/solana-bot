
import os, time, redis, pandas as pd

REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
METRICS_PATH = os.getenv("LAT_METRICS","/app/metrics_latency.csv")
KEY = os.getenv("CU_MULT_KEY","cu:mult")
KEY_FEE = os.getenv("PF_MULT_KEY","pf:mult")

# Bounds
MIN_M = float(os.getenv("CU_MULT_MIN","0.8"))
MAX_M = float(os.getenv("CU_MULT_MAX","2.0"))
MIN_PF = float(os.getenv("PF_MULT_MIN","0.8"))
MAX_PF = float(os.getenv("PF_MULT_MAX","2.5"))

r = redis.from_url(REDIS_URL)

def compute_mult():
    # Simple rule: if p95 quote > 120ms → increase CU & priority a bit; if < 60ms → decrease
    if not os.path.exists(METRICS_PATH):
        return 1.0, 1.0
    try:
        df = pd.read_csv(METRICS_PATH, header=None, names=['ts','k','v'])
        s = df[df['k']=='quote_ms']['v']
        if len(s)<50: return 1.0, 1.0
        p95 = float(s.quantile(0.95))
        if p95 > 180: return 1.2, 1.2
        if p95 > 120: return 1.1, 1.1
        if p95 < 60:  return 0.9, 0.9
        return 1.0, 1.0
    except Exception:
        return 1.0, 1.0

def clamp(x, lo, hi): return max(lo, min(hi, x))

def main():
    cm = 1.0; pf = 1.0
    while True:
        m1, p1 = compute_mult()
        cm = clamp(cm * m1, MIN_M, MAX_M)
        pf = clamp(pf * p1, MIN_PF, MAX_PF)
        try:
            r.set(KEY, str(round(cm,3)))
            r.set(KEY_FEE, str(round(pf,3)))
            print("[tuner] set cu:mult=", cm, " pf:mult=", pf)
        except Exception:
            pass
        time.sleep(30)

if __name__=="__main__":
    main()


import os, time, pandas as pd, redis
from dotenv import load_dotenv
load_dotenv()

REDIS_URL=os.getenv("REDIS_URL","redis://redis:6379/0")
CSV_PATH=os.getenv("CSV_PATH","/app/analytics.csv")
EV_KEY="hint:cross_ev_thr_bps"
SIZE_KEY="hint:size_mult"

r=redis.from_url(REDIS_URL)

def compute_hints(df):
    # simple heuristic: if accept% < 0.6, raise EV threshold; if fee burn high, reduce size
    accept = float(r.get("bundle:accept_rate") or 0)
    fee = float(r.get("hb:fee_burn:day") or 0)
    pnl = float(r.get("hb:pnl:day") or 0)
    fee_ratio = (fee/pnl) if pnl>0 else 0.0

    ev = 7.0
    size_mult = 1.0
    if accept < 0.6: ev += 2.0
    if fee_ratio > 0.4: size_mult *= 0.7

    return round(ev,2), round(size_mult,2)

def loop():
    while True:
        try:
            if os.path.exists(CSV_PATH):
                df = pd.read_csv(CSV_PATH)
            else:
                df = pd.DataFrame()
            ev, sz = compute_hints(df)
            r.set(EV_KEY, ev)
            r.hset("ops_guard:state","size_mult", sz)
            print(f"[TUNER] Set {EV_KEY}={ev}, size_mult={sz}")
        except Exception as e:
            print("tuner error:", e)
        time.sleep(60)

if __name__=="__main__":
    loop()

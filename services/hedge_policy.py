
import os, time, csv, statistics, redis
METRICS_PATH = os.getenv("METRICS_PATH","metrics.csv")
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
WINDOW = int(os.getenv("HEDGE_POLICY_WINDOW","800"))
# Bounds for dynamic config
PRIO_MIN, PRIO_MAX = 0.3, 0.9
SLIP_MIN, SLIP_MAX = 60, 200
COOL_MIN, COOL_MAX = 1, 6

def tail_rows(n=4000):
    try:
        with open(METRICS_PATH,"r") as f:
            rd=csv.DictReader(f)
            rows=list(rd)[-n:]
            return rows
    except Exception:
        return []

def calc_defaults(rows):
    xs=[float(x.get("pnl_usd") or 0) for x in rows if x.get("kind") in ("trade_fill","trade_loss")]
    if len(xs)<20:
        return 0.5, 100, 2
    mean=sum(xs)/len(xs)
    vol=statistics.pstdev(xs) if len(xs)>1 else 1.0
    # Heuristic: when mean<0 and vol high -> cool down & raise slippage cap but lower prio
    risk = min(1.0, max(0.0, (vol - abs(mean)) / max(1e-6, vol+abs(mean)) ))
    prio = max(PRIO_MIN, min(PRIO_MAX, 0.7 - 0.3*risk))
    slip = int(max(SLIP_MIN, min(SLIP_MAX, 100 + 60*risk)))
    cool = int(max(COOL_MIN, min(COOL_MAX, 2 + 3*risk)))
    return prio, slip, cool

def main():
    while True:
        rows = tail_rows()
        prio, slip, cool = calc_defaults(rows)
        # write default dynamic cfg
        r.set("hsbot:hedge:cfg:prio_mult:default", f"{prio:.3f}")
        r.set("hsbot:hedge:cfg:max_slippage_bps:default", str(slip))
        r.set("hsbot:hedge:cfg:cooldown:default", str(cool))
        time.sleep(2)

if __name__=="__main__":
    main()

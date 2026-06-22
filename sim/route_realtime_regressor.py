
import os, csv, time, redis, statistics, json
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
METRICS_PATH = os.getenv("METRICS_PATH","metrics.csv")
WINDOW = int(os.getenv("RTR_WINDOW","800"))
BAD_PNL = float(os.getenv("RTR_BADPNL","-5.0"))
BAD_WIN = float(os.getenv("RTR_BADWIN","0.38"))
def tail_rows(n=4000):
    try:
        import csv as _csv
        with open(METRICS_PATH,"r") as f:
            rd = _csv.DictReader(f)
            rows = list(rd)[-n:]
        return rows
    except Exception:
        return []
def score_route(rows, route):
    xs = [float(x.get("pnl_usd") or 0) for x in rows if (x.get("kind") in ("trade_fill","trade_loss") and (x.get("route") or "route")==route)]
    if not xs: return 0.0, 0.0, 0.0
    last = xs[-WINDOW:]
    win = sum(1 for z in last if z>0)/max(1,len(last))
    mean = sum(last)/max(1,len(last))
    vol = statistics.pstdev(last) if len(last)>1 else 0.0
    return mean, vol, win
def main():
    while True:
        rows = tail_rows()
        routes = sorted({x.get("route") or "route" for x in rows if x.get("kind") in ("trade_fill","trade_loss")})
        bad = []
        for rt in routes:
            m,v,w = score_route(rows, rt)
            if m < BAD_PNL or w < BAD_WIN:
                bad.append(rt)
        if bad:
            r.set("hsbot:route:blacklist", json.dumps(bad))
        time.sleep(1.0)
if __name__ == "__main__":
    main()

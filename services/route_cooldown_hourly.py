
import os, time, csv, redis
from datetime import datetime

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
WIN_SEC = int(os.getenv("ROUTE_COOLDOWN_WINDOW_SEC","900"))
COOL_SEC = int(os.getenv("ROUTE_COOLDOWN_SEC","600"))
BAD_THRESH = float(os.getenv("ROUTE_BAD_PNLPS","-0.5"))
GOOD_EXIT = float(os.getenv("ROUTE_GOOD_EXIT_PNLPS","0.2"))
MIN_TRADES_EXIT = int(os.getenv("ROUTE_MIN_TRADES_EXIT","3"))
DECAY = float(os.getenv("ROUTE_PNL_DECAY","0.95"))
LOG="logs/executions.csv"

def hour_bucket(ts):
    return datetime.utcfromtimestamp(float(ts)).strftime("%H")

def main():
    last_m=0
    while True:
        try:
            if not os.path.exists(LOG): time.sleep(5); continue
            m=os.path.getmtime(LOG)
            if m==last_m: time.sleep(5); continue
            last_m=m
            # Aggregate per route per hour
            agg={}; trades={}
            with open(LOG,"r") as f:
                for row in csv.DictReader(f):
                    try:
                        route=row.get("route_label") or "unknown"
                        gross=float(row.get("pnl_gross","0") or 0)
                        fee=float(row.get("priority_fee","0") or 0)+float(row.get("rpc_fee","0") or 0)
                        tsd=float(row.get("ts_detect","0") or 0); tss=float(row.get("ts_submit","0") or 0)
                        dur=max(0.001, (tss or tsd) - tsd); ts=tss or tsd
                        if (time.time()-ts)>WIN_SEC: continue
                        hr=hour_bucket(ts)
                        key=(route,hr)
                        pnlps=(gross-fee)/dur
                        agg[key]= agg.get(key,0.0)*DECAY + pnlps*(1-DECAY)
                        trades[key]= trades.get(key,0)+1
                    except: pass
            # Apply cooldown & smart exit
            for (route,hr), v in agg.items():
                if v<=BAD_THRESH:
                    r.setex(f"hsbot:route_cool:{route}", COOL_SEC, 1)
                else:
                    # exit cooldown if enough trades in hour and pnlps above threshold
                    if trades.get((route,hr),0)>=MIN_TRADES_EXIT and v>=GOOD_EXIT:
                        r.delete(f"hsbot:route_cool:{route}")
        except Exception:
            pass
        time.sleep(5)

if __name__=="__main__":
    main()

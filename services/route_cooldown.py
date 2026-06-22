import os, time, csv, redis
r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
WIN_SEC = int(os.getenv("ROUTE_COOLDOWN_WINDOW_SEC","900"))
PNL_DECAY = float(os.getenv("ROUTE_PNL_DECAY","0.95"))
BAD_THRESH = float(os.getenv("ROUTE_BAD_PNLPS","-0.5"))
COOL_SEC = int(os.getenv("ROUTE_COOLDOWN_SEC","600"))
LOG="logs/executions.csv"
def main():
    last_mtime=0
    while True:
        try:
            if not os.path.exists(LOG):
                time.sleep(5); continue
            mt = os.path.getmtime(LOG)
            if mt==last_mtime:
                time.sleep(5); continue
            last_mtime=mt
            pnlps={}
            import csv, time
            with open(LOG,"r") as f:
                for row in csv.DictReader(f):
                    route=row.get("route_label") or "unknown"
                    gross=float(row.get("pnl_gross","0") or 0)
                    fee=float(row.get("priority_fee","0") or 0)+float(row.get("rpc_fee","0") or 0)
                    tsd=float(row.get("ts_detect","0") or 0); tss=float(row.get("ts_submit","0") or 0)
                    dur=max(0.001, tss-tsd); ts=tss or tsd
                    if (time.time()-ts)>WIN_SEC: continue
                    pnlps.setdefault(route,0.0)
                    pnlps[route]= pnlps[route]*PNL_DECAY + ((gross-fee)/dur)*(1-PNL_DECAY)
            for route,val in pnlps.items():
                if val<=BAD_THRESH:
                    r.setex(f"hsbot:route_cool:{route}", COOL_SEC, 1)
        except Exception:
            pass
        time.sleep(5)
if __name__=="__main__": main()

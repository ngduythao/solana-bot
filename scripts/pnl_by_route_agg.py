#!/usr/bin/env python3
import os, csv, time, redis, json
from datetime import datetime

OUT="logs/pnl_by_route.csv"
FIELDS=["ts","route","pair","attempts","fills","win_pct","latency_p50_ms","latency_p95_ms","net_pnl_usd"]

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def read_metrics():
    # This is best-effort; if your engine pushes trade metrics into Redis,
    # adapt the keys below. We fall back to zeros if not found.
    routes = r.smembers("hsbot:routes:seen") or []
    data=[]
    for route in routes:
        base=f"hsbot:route:{route}"
        pair = r.get(base+":pair") or ""
        attempts = int(r.get(base+":attempts") or 0)
        fills = int(r.get(base+":fills") or 0)
        win = float(r.get(base+":win_pct") or (100.0*fills/max(attempts,1)))
        p50 = float(r.get(base+":lat_p50") or 0)
        p95 = float(r.get(base+":lat_p95") or 0)
        pnl = float(r.get(base+":net_pnl_usd") or 0)
        data.append((route,pair,attempts,fills,win,p50,p95,pnl))
    return data

def ensure_header(path):
    if not os.path.exists(path):
        with open(path,"w",newline="") as f:
            w=csv.writer(f)
            w.writerow(FIELDS)

def write_snapshot():
    ensure_header(OUT)
    now=int(time.time())
    rows=read_metrics()
    with open(OUT,"a",newline="") as f:
        w=csv.writer(f)
        for route,pair,attempts,fills,win,p50,p95,pnl in rows:
            w.writerow([now,route,pair,attempts,fills,round(win,2),round(p50,1),round(p95,1),round(pnl,4)])

if __name__=="__main__":
    while True:
        try:
            write_snapshot()
        except Exception as e:
            pass
        time.sleep(30)

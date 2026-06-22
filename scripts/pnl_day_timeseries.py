#!/usr/bin/env python3
import os, time, csv, redis
from datetime import datetime

OUT="logs/pnl_day_timeseries.csv"
FIELDS=["ts","pnl_day_pct"]

r=redis.Redis(host='localhost', port=6379, decode_responses=True)

def ensure_header():
    if not os.path.exists(OUT):
        os.makedirs("logs", exist_ok=True)
        with open(OUT,"w",newline="") as f:
            csv.writer(f).writerow(FIELDS)

def loop():
    ensure_header()
    while True:
        try:
            v = r.get("hsbot:pnl:day_pct")
            if v is not None:
                with open(OUT,"a",newline="") as f:
                    csv.writer(f).writerow([int(time.time()), float(v)])
        except Exception:
            pass
        time.sleep(60)

if __name__=="__main__":
    loop()

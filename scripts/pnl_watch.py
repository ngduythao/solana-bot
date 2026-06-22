#!/usr/bin/env python3
import time, os, redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def notify(msg):
    os.system(f"./scripts/tg_notify.sh \"{msg}\" >/dev/null 2>&1")

def loop():
    last_min = float(r.get("hsbot:pnl:minute_usd") or 0)
    last_hour = float(r.get("hsbot:pnl:hour_usd") or 0)
    while True:
        cur_min = float(r.get("hsbot:pnl:minute_usd") or 0)
        cur_hour = float(r.get("hsbot:pnl:hour_usd") or 0)
        if last_min>0 and (cur_min-last_min)/last_min < -0.10:
            notify(f"⚠️ PnL drop >10% last minute: {cur_min} vs {last_min}")
        if last_hour>0 and (cur_hour-last_hour)/last_hour < -0.20:
            notify(f"⚠️ PnL drop >20% last hour: {cur_hour} vs {last_hour}")
        last_min, last_hour = cur_min, cur_hour
        time.sleep(60)

if __name__=='__main__':
    loop()

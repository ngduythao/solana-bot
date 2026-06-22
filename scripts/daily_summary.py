#!/usr/bin/env python3
import os, time, datetime as dt, redis

r=redis.Redis(host='localhost', port=6379, decode_responses=True)
TZ_OFFSET = 7  # Vietnam UTC+7

def now_vn():
    return dt.datetime.utcnow() + dt.timedelta(hours=TZ_OFFSET)

def tg(msg):
    os.system(f"./scripts/tg_notify.sh \"{msg}\" >/dev/null 2>&1")

def loop():
    while True:
        n = now_vn()
        key = f"daily_summary_sent:{n.date()}"
        if n.hour == 7 and not r.get(key):
            pnl = r.get("hsbot:pnl:daily_usd") or "0"
            trades = r.get("hsbot:trades:count") or "0"
            wr = r.get("hsbot:trades:wr") or "0"
            tipm = r.get("hsbot:jito:tip_mult") or "1"
            msg = f"📊 Daily Summary {n.date()} (VN 07:00)\\nPnL: ${pnl}\\nTrades: {trades}\\nWinRate: {wr}%\\nTipMult: {tipm}"
            tg(msg)
            r.setex(key, 36*3600, "1")
        time.sleep(60)
if __name__=='__main__':
    loop()

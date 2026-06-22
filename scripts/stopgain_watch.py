#!/usr/bin/env python3
import os, time, redis
r=redis.Redis(host='localhost', port=6379, decode_responses=True)
BASE = float(os.environ.get("BASE_EQUITY_USD","10000"))
PCT  = float(os.environ.get("STOPGAIN_DAILY_PCT","10"))  # default +10%
THRESH_USD = abs(BASE*PCT/100.0)
def tg(msg): os.system(f"./scripts/tg_notify.sh \"{msg}\" >/dev/null 2>&1")
def loop():
    while True:
        try: pnl = float(r.get("hsbot:pnl:daily_usd") or 0.0)
        except: pnl = 0.0
        paused = bool(r.get("hsbot:paused"))
        if pnl >= THRESH_USD and not paused:
            r.set("hsbot:paused","1")
            r.set("hsbot:stopgain:tripped","1")
            tg(f"✅ Daily Take-Profit hit (+{PCT:.1f}% of ${BASE:.0f} → +{THRESH_USD:.0f} USD). Bot paused. pnl_daily={pnl:.2f}")
        time.sleep(15)
if __name__=='__main__': loop()

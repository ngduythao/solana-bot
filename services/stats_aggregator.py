
import os, time, csv, redis

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
AN_FILE = os.getenv("ANALYTICS_FILE","analytics.csv")
EX_FILE = os.getenv("EXEC_FILE","logs/executions.csv")

def tail_numbers(path):
    gross = 0.0; burn = 0.0; hit=0; miss=0
    if os.path.exists(path):
        with open(path,"r") as f:
            for row in csv.DictReader(f):
                g = float(row.get("pnl_gross","0") or 0)
                b = float(row.get("priority_fee","0") or 0) + float(row.get("rpc_fee","0") or 0)
                s = row.get("status","")
                gross += g; burn += b
                if s=="ok": hit += 1
                else: miss += 1
    return gross, burn, hit, miss

def main():
    print("[stats_aggregator] running")
    while True:
        g1,b1,h1,m1 = tail_numbers(AN_FILE)
        g2,b2,h2,m2 = tail_numbers(EX_FILE) if os.path.exists(EX_FILE) else (0,0,0,0)
        gross = g1+g2; burn = b1+b2; hit=h1+h2; miss=m1+m2
        r.set("hsbot:stats:gross_pnl", gross)
        r.set("hsbot:stats:fee_burn", burn)
        r.set("hsbot:stats:hit", hit)
        r.set("hsbot:stats:miss", miss)
        update_windows()
        update_today_pnl(gross)
        time.sleep(5)

if __name__=="__main__":
    main()


import time
from datetime import datetime, timezone

def update_windows():
    # For simplicity, we use total deltas every tick as window approx (production should track timestamps)
    hit = int(float(r.get("hsbot:stats:hit") or 0))
    miss = int(float(r.get("hsbot:stats:miss") or 0))
    prev_hit = int(float(r.get("hsbot:stats:hit_prev") or 0))
    prev_miss = int(float(r.get("hsbot:stats:miss_prev") or 0))
    r.set("hsbot:stats:hit_window", max(0, hit - prev_hit))
    r.set("hsbot:stats:miss_window", max(0, miss - prev_miss))
    r.set("hsbot:stats:hit_prev", hit)
    r.set("hsbot:stats:miss_prev", miss)

def update_today_pnl(gross):
    # naive: store cumulative gross today (reset at UTC 00:00)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cur_day = r.get("hsbot:stats:day") or b""
    if cur_day.decode() != today:
        r.set("hsbot:stats:day", today)
        r.set("hsbot:stats:gross_pnl_today", 0.0)
    r.incrbyfloat("hsbot:stats:gross_pnl_today", gross)


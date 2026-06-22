
import os, time, json, csv, redis
from collections import deque
from datetime import datetime, timedelta

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
WIN = int(os.getenv("WINDOW_SEC","300"))
FAIL_CAP = float(os.getenv("FAIL_RATE_CAP_PCT","15"))
REJ_CAP = float(os.getenv("BUNDLE_REJECT_CAP_PCT","20"))
FAIL_HARD = int(os.getenv("FAIL_RATE_HARD_PAUSE_WINDOWS","3"))
REJ_HARD = int(os.getenv("BUNDLE_REJECT_HARD_PAUSE_WINDOWS","3"))
DAILY_WARN = int(os.getenv("DAILY_WARN_BPS","50"))
DAILY_STOP = int(os.getenv("DAILY_STOP_BPS","100"))

def pct(a,b): 
    return (a/max(1.0,b))*100.0

def window_loop():
    fail_hist = deque(maxlen=1000)
    rej_hist = deque(maxlen=1000)
    fail_bad = 0
    rej_bad = 0
    last_check = 0
    while True:
        now = time.time()
        # consume executions.csv tail via stats_aggregator already; here we use rolling in Redis (optional future)
        # For simplicity, rely on hit/miss counters incremented elsewhere + bundle_events
        # Evaluate fail-rate in last WIN seconds from a Redis list holding timestamps of fail/total (optional simplified):
        # We'll estimate via keys updated by stats_aggregator: hsbot:stats:hit_window, miss_window
        try:
            hit = float(r.get("hsbot:stats:hit_window") or 0)
            miss = float(r.get("hsbot:stats:miss_window") or 0)
            total = hit+miss
            fr = pct(miss,total)
            if fr > FAIL_CAP:
                fail_bad += 1
                # reduce size & pf_mult softly
                pf = float(r.get("hsbot:cfg:pf_mult") or 1.0)
                pf = max(0.5, pf*0.8)
                r.set("hsbot:cfg:pf_mult", pf)
                r.publish("hsbot:alerts", json.dumps({"type":"fail_rate_window","fr":fr,"action":"pf_down"}))
                # optional size cap could be enforced via size bps key
                r.set("hsbot:cfg:size_nav_bps_override",  max(10, int((float(os.getenv("SIZE_MAX_NAV_BPS","50")))*0.5)) )
            else:
                fail_bad = max(0, fail_bad-1)
            # bundle reject rate
            # compute from last N bundle events accepted/rejected in last WIN sec
            # Simplified: counters must be updated by jito_manager; here we read keys:
            acc = float(r.get("hsbot:bundle:accepted_window") or 0)
            rej = float(r.get("hsbot:bundle:rejected_window") or 0)
            brej = pct(rej, acc+rej)
            if brej > REJ_CAP:
                rej_bad += 1
                # lower pf_mult, maybe switch relay (set a flag)
                pf = float(r.get("hsbot:cfg:pf_mult") or 1.0)
                pf = max(0.5, pf*0.8)
                r.set("hsbot:cfg:pf_mult", pf)
                r.set("hsbot:cfg:switch_relay", 1)
                r.publish("hsbot:alerts", json.dumps({"type":"bundle_reject_window","br":brej,"action":"pf_down_switch"}))
            else:
                rej_bad = max(0, rej_bad-1)
            if fail_bad >= FAIL_HARD or rej_bad >= REJ_HARD:
                r.set("hsbot:pause", 1)
                r.publish("hsbot:alerts", json.dumps({"type":"hard_pause","reason":"risk_windows"}))
        except Exception as e:
            pass

        # daily DD thresholds
        try:
            nav0 = float(r.get("hsbot:cfg:nav_usd") or 10000.0)
            gross = float(r.get("hsbot:stats:gross_pnl_today") or 0.0)
            dd_bps = max(0.0, -gross)*1e4/nav0 if gross<0 else 0.0
            if dd_bps >= DAILY_STOP:
                r.set("hsbot:pause", 1)
                r.publish("hsbot:alerts", json.dumps({"type":"daily_stop","dd_bps":dd_bps}))
            elif dd_bps >= DAILY_WARN:
                r.publish("hsbot:alerts", json.dumps({"type":"daily_warn","dd_bps":dd_bps}))
        except Exception:
            pass

        time.sleep(5)

if __name__=="__main__":
    window_loop()

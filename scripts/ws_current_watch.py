#!/usr/bin/env python3
import time, os, redis
r=redis.Redis(host='localhost', port=6379, decode_responses=True)

def notify(msg):
    try:
        os.system(f"./scripts/tg_notify.sh \"{msg}\" >/dev/null 2>&1")
    except Exception:
        pass

def loop():
    last = r.get("ws:current") or ""
    while True:
        cur = r.get("ws:current") or ""
        if cur and cur != last:
            notify(f"🔄 WS switched → {cur}")
            last = cur
        time.sleep(2)

if __name__=='__main__':
    loop()

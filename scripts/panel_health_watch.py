#!/usr/bin/env python3
import os, time, requests

def tg(msg):
    tok=(os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chats=((os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_IDS") or "")).strip()
    if not tok or not chats: return
    for chat in [c.strip() for c in chats.split(",") if c.strip()]:
        try:
            requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", timeout=5, json={"chat_id": chat, "text": msg})
        except Exception:
            pass

def ok():
    try:
        for path in ("/", "/analytics/pnl_status", "/guard/check"):
            r=requests.get("http://127.0.0.1:8080"+path, timeout=3)
            if r.status_code!=200: return False
        return True
    except Exception:
        return False

def main():
    fail=0
    while True:
        if ok():
            fail=0
        else:
            fail+=1
            if fail==10:  # ~5 minutes if 30s interval
                tg("⚠️ Panel health failing for ~5 minutes")
        time.sleep(30)

if __name__=="__main__":
    main()

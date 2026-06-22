#!/usr/bin/env python3
import os, time, redis, requests, datetime as dt

r=redis.Redis(host='localhost', port=6379, decode_responses=True)

def tg(msg:str):
    tok=(os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chats=((os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_IDS") or "")).strip()
    if not tok or not chats: return
    for chat in [c.strip() for c in chats.split(",") if c.strip()]:
        try:
            requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", timeout=5, json={"chat_id": chat, "text": msg})
        except Exception:
            pass

def next_7am_vn_epoch():
    # VN is UTC+7
    now_utc=dt.datetime.utcnow()
    vn=now_utc+dt.timedelta(hours=7)
    target=vn.replace(hour=7, minute=0, second=0, microsecond=0)
    if vn >= target:
        target=target+dt.timedelta(days=1)
    # convert back to UTC epoch
    target_utc=target-dt.timedelta(hours=7)
    return int(target_utc.timestamp())

def loop():
    while True:
        try:
            base=float(r.get("hsbot:equity:day_base_usd") or 0.0)
            cur=float(r.get("hsbot:equity:now_usd") or 0.0)
            pnl_usd=cur-base if base>0 and cur>0 else float(r.get("hsbot:pnl:day_usd") or 0.0)
            pnl_pct= (pnl_usd/base*100.0) if base>0 else float(r.get("hsbot:pnl:day_pct") or 0.0)
            routes=int(r.get("hsbot:routes:tried_today") or 0)
            ok=int(r.get("hsbot:routes:ok_today") or 0)
            halts=int(r.get("hsbot:risk:halts_today") or 0)
            date=(dt.datetime.utcnow()+dt.timedelta(hours=7)).strftime("%Y-%m-%d")
            msg=(f"📊 Daily Summary ({date})\n"
                 f"• Net PnL: {pnl_usd:+.2f} USD ({pnl_pct:+.2f}%)\n"
                 f"• Routes: {routes} tried, {ok} ok\n"
                 f"• Risk halts: {halts}")
            # sleep to next 07:00 VN
            now=int(time.time())
            nxt=next_7am_vn_epoch()
            time.sleep(max(0, nxt-now))
            tg(msg)
            # after sending, wait 60s to avoid duplicate sends
            time.sleep(60)
        except Exception:
            time.sleep(30)

if __name__=="__main__":
    loop()

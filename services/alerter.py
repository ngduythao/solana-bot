
import os, json, time, httpx, redis

ENABLE = os.getenv("ALERTS_ENABLE","1")=="1"
BOT = os.getenv("TELEGRAM_BOT_TOKEN","")
CHAT = os.getenv("TELEGRAM_CHAT_ID","")
URL = f"https://api.telegram.org/bot{BOT}/sendMessage"

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))

def send(msg: str):
    if not ENABLE or not BOT or not CHAT: 
        return
    try:
        with httpx.Client(timeout=5.0) as c:
            c.post(URL, data={"chat_id": CHAT, "text": msg})
    except Exception as e:
        print("telegram send error", e)

def loop():
    pubsub = r.pubsub()
    pubsub.subscribe("hsbot:alerts")
    for it in pubsub.listen():
        if it["type"] != "message": 
            continue
        try:
            ev = json.loads(it["data"])
            t = ev.get("type","event")
            send(f"[{t}] {ev}")
        except Exception as e:
            print("alerter parse error", e)

if __name__=="__main__":
    print("[alerter] running")
    loop()

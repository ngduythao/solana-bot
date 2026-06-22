
import os, time, json, redis, hashlib
try:
    import requests
except Exception:
    requests = None

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

BOT=os.getenv("TELEGRAM_BOT_TOKEN","")
CHAT=os.getenv("TELEGRAM_CHAT_ID","")
SILENT=os.getenv("TELEGRAM_SILENT","0")=="1"
MIN_SEV=os.getenv("TELEGRAM_MIN_SEVERITY","warn")  # debug|info|warn|error|critical
SEV_ORDER={"debug":0,"info":1,"warn":2,"error":3,"critical":4}
POLL_INT=float(os.getenv("TELEGRAM_POLL_INTERVAL","4"))

STATE_KEY="solbot:alerts:last_ts"
DEDUP_TTL=3600  # seconds

def should_send(sev:str)->bool:
    return SEV_ORDER.get(sev,2) >= SEV_ORDER.get(MIN_SEV,2)

def send(msg:str):
    if not BOT or not CHAT or requests is None:
        return False, "not_configured"
    url=f"https://api.telegram.org/bot{BOT}/sendMessage"
    data={"chat_id": CHAT, "text": msg[:4000], "disable_notification": SILENT, "parse_mode": "HTML"}
    try:
        resp=requests.post(url, data=data, timeout=5)
        ok=resp.status_code==200 and resp.json().get("ok",False)
        return ok, resp.text[:120]
    except Exception as e:
        return False, str(e)

def main():
    print("[telegram_notifier] running")
    try:
        last=float(r.get(STATE_KEY) or 0.0)
    except Exception:
        last=0.0
    while True:
        try:
            arr=r.lrange("solbot:alerts",0,50)
            # alerts are newest at head; we scan reverse to deliver oldest-first
            for it in reversed(arr):
                try:
                    j=json.loads(it)
                except Exception:
                    continue
                ts=float(j.get("ts",0)); sev=j.get("sev","warn"); m=j.get("msg","")
                if ts<=last or not should_send(sev): continue
                # dedup by hash
                h=hashlib.sha256((sev+"|"+m).encode()).hexdigest()
                if r.getex(f"solbot:tg:d:{h}", DEDUP_TTL) is None:
                    # fallback if server Redis version doesn't support GETEX
                    if not r.setnx(f"solbot:tg:d:{h}", "1"):
                        continue
                    r.expire(f"solbot:tg:d:{h}", DEDUP_TTL)
                ok, info=send(f"🔔 <b>{sev.upper()}</b> • {m}")
                r.lpush("solbot:alerts:tg", json.dumps({"ts":time.time(),"sent":ok,"info":info,"sev":sev,"msg":m}))
                r.ltrim("solbot:alerts:tg",0,50)
                last=ts
                r.set(STATE_KEY, str(last))
        except Exception:
            pass
        time.sleep(POLL_INT)

if __name__=="__main__":
    main()

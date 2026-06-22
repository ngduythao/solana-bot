
#!/usr/bin/env python3
import os, time, redis, json, urllib.request, urllib.parse

BOT=os.getenv("TG_BOT_TOKEN","")
CHAT=os.getenv("TG_CHAT_ID","")
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
P95_THRESH=float(os.getenv("ALERT_P95_MS","160"))
WR_BAD=float(os.getenv("ALERT_WR_BAD","0.45"))
PNL_BAD=float(os.getenv("ALERT_PNL_HOURLY_BAD","-50"))
POLL=int(os.getenv("ALERT_POLL_SEC","30"))
r=redis.from_url(REDIS_URL)

def send(msg):
    if not BOT or not CHAT: return
    text=urllib.parse.quote(msg)
    url=f"https://api.telegram.org/bot{BOT}/sendMessage?chat_id={CHAT}&text={text}&parse_mode=Markdown"
    try:
        urllib.request.urlopen(url, timeout=3).read()
    except Exception:
        pass

def main():
    last={}
    while True:
        try:
            p95=float(r.get("hsbot:notional:last_p95") or 0)
            tip=float(r.get("hsbot:tip:mult_effective") or 0)
            mult=float(r.get("hsbot:notional:mult_effective") or 0)
            # basic event: p95 too high
            if p95>=P95_THRESH and last.get("p95")!=int(p95):
                send(f"⚠️ p95 latency {p95:.1f}ms — tip={tip:.2f}, notional_mult={mult:.2f}")
                last["p95"]=int(p95)
        except Exception:
            pass
        time.sleep(POLL)

if __name__=="__main__":
    main()

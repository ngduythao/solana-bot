
import os, time, json, httpx, redis

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

TG_TOKEN = os.getenv("TG_BOT_TOKEN","")
TG_CHAT  = os.getenv("TG_CHAT_ID","")
WEBHOOK  = os.getenv("GENERIC_WEBHOOK","")

def notify(msg: str):
    try:
        if TG_TOKEN and TG_CHAT:
            url=f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            with httpx.Client(timeout=3.0) as c:
                c.post(url, data={"chat_id":TG_CHAT,"text":msg[:4000]})
        if WEBHOOK:
            with httpx.Client(timeout=3.0) as c:
                c.post(WEBHOOK, json={"text":msg, "ts":time.time()})
    except Exception:
        pass

def main():
    print("[notifier] running")
    keys=["jito:relay_stats:*"]
    last_tip=None
    while True:
        # circuit breaker alerts
        for k in r.scan_iter(match='jito:relay_stats:*'):
            h=r.hgetall(k)
            if h:
                p95=float(h.get(b'p95_ms',b'0'))
                p50=float(h.get(b'p50_ms',b'0'))
                if p50>0 and p95/p50>2.5:
                    notify(f'[latency spike] {k.decode()} p95/p50={p95/p50:.2f}')
        try:
            tips = r.get("jito:tip_suggest:last_hour")
            if tips and tips != last_tip:
                notify(f"[tip] {tips.decode()}")
                last_tip = tips
            ev = r.lindex("solbot:reconcile", 0)
            if ev:
                e = json.loads(ev)
                if abs(e.get("delta",0)) > 1_000_000:  # threshold lamports
                    notify(f"[reconcile] big delta: {e}")
        except Exception as e:
            pass
        time.sleep(10)

if __name__ == "__main__":
    main()

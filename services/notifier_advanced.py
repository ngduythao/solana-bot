
import os, time, json, httpx, redis, statistics

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

TG_TOKEN = os.getenv("TG_BOT_TOKEN",""); TG_CHAT  = os.getenv("TG_CHAT_ID","")
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

def p95_spike():
    vals=[]
    for k in r.scan_iter(match="jito:relay_stats:*"):
        if k.decode().endswith(":leaders"): continue
        try:
            p95=float(r.hget(k,"p95_ms") or 0); vals.append(p95)
        except: pass
    if len(vals)>=2:
        med=statistics.median(vals); mx=max(vals)
        if mx>0 and med>0 and mx/med>2.0:
            return f"p95 spike: max={mx:.0f}ms median={med:.0f}ms"
    return None

def circuit_tripped():
    # jito_client stores circuit state in-memory; here we infer from failure streak in stats (approx)
    return None

def ev_anomaly():
    arr=[]
    for i in range(30):
        it=r.lindex("solbot:reconcile", i)
        if not it: break
        try:
            arr.append(abs(json.loads(it).get("delta",0)))
        except: pass
    if len(arr)>=10 and (sum(arr[:10])>10*1_000_000):
        return "EV anomaly: |delta| sum(10) unusually high"
    return None

def main():
    print("[notifier_adv] running")
    last=None
    while True:
        try:
            for fn in (p95_spike, ev_anomaly):
                msg = fn()
                if msg and msg!=last:
                    notify("[alert] "+msg)
                    last=msg
        except Exception as e:
            pass
        time.sleep(12)

if __name__ == "__main__":
    main()

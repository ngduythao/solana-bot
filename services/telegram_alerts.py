
import os, time, json, redis, httpx

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)
BOT=os.getenv("TELEGRAM_BOT_TOKEN","")
CHAT=os.getenv("TELEGRAM_CHAT_ID","")

def send(msg:str):
    if not BOT or not CHAT: return
    try:
        with httpx.Client(timeout=3) as c:
            c.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id": CHAT, "text": msg})
    except Exception: pass

def fmt_pct(x): 
    try: return f"{x*100:.2f}%"
    except: return "n/a"

def main():
    print("[alerts] running")
    last={}
    while True:
        try:
            slo=json.loads(r.get("solbot:slo") or b'{}')
            pnl=json.loads(r.get("solbot:pnl:per_pool") or b'{}')
            acc=float(slo.get("p99_ms",0)); miss=float(slo.get("miss_rate",0.0))
            ok=slo.get("ok", False)
            # trigger on not ok or sharp change
            if not ok or miss>0.2:
                send(f"[SLO] not OK — p99={acc}ms miss={fmt_pct(miss)}")
            # daily pnl summary (every ~1h send once)
            now=int(time.time()//3600)
            if last.get("hr")!=now:
                last["hr"]=now
                tot=sum(pnl.values()) if isinstance(pnl, dict) else 0
                send(f"[PnL] last snapshot per pool: {pnl} | total={tot}")
            # queue pressure
            q1=int(r.llen("autohedge:ix_req") or 0); q2=int(r.llen("autohedge:cancel_req") or 0)
            if q1>900 or q2>900: send(f"[Queue] High pressure ix={q1} cancel={q2}")
        except Exception: pass
        time.sleep(30)

if __name__=="__main__":
    main()

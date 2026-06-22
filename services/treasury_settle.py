
import os, time, json, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
REGION=os.getenv("REGION","nj-us")
SETTLE_PERIOD=int(os.getenv("SETTLE_PERIOD_SEC","86400"))

def main():
    print("[treasury_settle] running")
    last=0
    while True:
        try:
            now=time.time()
            if now-last>SETTLE_PERIOD:
                # read PnL attribution (best-effort)
                attrib=json.loads(r.get("solbot:pnl_attrib") or b"{}").get("total",{})
                ev=float(attrib.get("ev",0.0))
                if ev>0:
                    # plan sweeping profits into vault
                    plan={"ts":now,"region":REGION,"kind":"sweep_profit_to_vault","amount_usdc":ev}
                    r.setex("solbot:treasury:settle", 300, json.dumps(plan))
                last=now
        except Exception:
            pass
        time.sleep(10)

if __name__=="__main__":
    main()

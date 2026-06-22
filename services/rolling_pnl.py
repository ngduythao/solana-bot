
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
ALPHA=float(os.getenv("ROLLING_PNL_ALPHA","0.2"))
def main():
    print("[rolling_pnl] running")
    ewma=0.0
    while True:
        try:
            tot=json.loads(r.get("solbot:pnl_attrib") or b"{}").get("total",{})
            ev=float(tot.get("ev",0.0))
            ewma = ALPHA*ev + (1-ALPHA)*ewma
            r.setex("solbot:rolling_pnl", 30, str(ewma))
        except Exception: pass
        time.sleep(5)
if __name__=="__main__":
    main()

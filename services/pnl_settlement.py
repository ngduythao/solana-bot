
import os, time, json, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
RESET=86400

def main():
    print("[pnl_settlement] running")
    last=time.time()
    while True:
        try:
            now=time.time()
            if now-last>RESET:
                evs=[]
                for i in range(300):
                    it=r.lindex("solbot:reconcile",i)
                    if not it: break
                    j=json.loads(it)
                    evs.append(int(j.get("delta",0)))
                pnl=sum(evs)
                r.lpush("solbot:treasury:settlement",json.dumps({"ts":now,"pnl":pnl}))
                last=now
        except Exception: pass
        time.sleep(60)

if __name__=="__main__":
    main()

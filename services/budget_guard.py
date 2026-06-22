
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
MAX_TIP_DAY=int(os.getenv("BUDGET_TIP_DAY","200000000"))   # lamports
MAX_FEE_DAY=int(os.getenv("BUDGET_FEE_DAY","100000000"))   # lamports
def main():
    print("[budget_guard] running")
    while True:
        try:
            tot={"tip":0,"fee":0}
            for i in range(500):
                it=r.lindex("solbot:reconcile",i)
                if not it: break
                j=json.loads(it); tot["tip"]+=int(j.get("tip_lamports",0)); tot["fee"]+=int(j.get("dex_fee",0))
            alert={}
            if tot["tip"]>MAX_TIP_DAY: alert["tip"]="exceed"
            if tot["fee"]>MAX_FEE_DAY: alert["fee"]="exceed"
            if alert: r.setex("solbot:budget:alert",60,json.dumps(alert))
        except Exception: pass
        time.sleep(30)
if __name__=="__main__": main()

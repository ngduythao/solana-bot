
import os, time, json, redis, statistics
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def main():
    print("[pnl_attrib] running")
    while True:
        try:
            N=400
            tot={"ev":0,"tip":0,"fee":0,"slip":0,"cu":0}
            per={}
            for i in range(N):
                it=r.lindex("solbot:reconcile", i)
                if not it: break
                j=json.loads(it)
                pair=j.get("pair","_all")
                d=per.setdefault(pair, {"ev":0,"tip":0,"fee":0,"slip":0,"cu":0})
                ev=int(j.get("delta",0))
                tip=float(j.get("tip_lamports",0)); fee=float(j.get("dex_fee",0))
                slp=float(j.get("slippage_bps",0)); cu=float(j.get("cu",0))
                for k,v in [("ev",ev),("tip",tip),("fee",fee),("slip",slp),("cu",cu)]:
                    d[k]+=v; tot[k]+=v
            r.setex("solbot:pnl_attrib", 30, json.dumps({"total":tot,"per_pair":per}))
        except Exception:
            pass
        time.sleep(5)

if __name__=="__main__":
    main()

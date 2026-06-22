
import os, json, redis, statistics, time
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def median(xs): 
    try: return statistics.median(xs) if xs else 0.0
    except: return 0.0
def main():
    print("[pnl_attr] running")
    while True:
        try:
            tips=[]; fees=[]; slips=[]; cu=[]; evs=[]
            for i in range(300):
                it=r.lindex("solbot:reconcile",i)
                if not it: break
                j=json.loads(it); tips.append(float(j.get("tip_lamports",0))); fees.append(float(j.get("dex_fee",0)))
                slips.append(float(j.get("slippage_bps",0))); cu.append(float(j.get("cu",0))); evs.append(int(j.get("delta",0)))
            out={"med_tip":median(tips),"med_fee":median(fees),"med_slip":median(slips),"med_cu":median(cu),"ev_med":median(evs)}
            r.setex("solbot:pnl_attr",30,json.dumps(out))
        except Exception: pass
        time.sleep(5)
if __name__=="__main__": main()

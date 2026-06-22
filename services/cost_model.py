
import os, time, json, redis, statistics
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def median(xs): 
    try: return statistics.median(xs) if xs else 0.0
    except: return 0.0

def main():
    print("[cost_model] running")
    while True:
        try:
            # pull last N reconcile entries and compute breakdown
            N=200
            tips=[]; fees=[]; cu=[]; slip=[]
            by_pair={}
            for i in range(N):
                it=r.lindex("solbot:reconcile", i)
                if not it: break
                j=json.loads(it)
                pair=j.get("pair","_all")
                tips.append(float(j.get("tip_lamports",0)))
                fees.append(float(j.get("dex_fee",0)))
                cu.append(float(j.get("cu",0)))
                slip.append(float(j.get("slippage_bps",0)))
                p=by_pair.setdefault(pair, {"tips":[],"fees":[],"cu":[],"slip":[],"ev":[]})
                p["tips"].append(float(j.get("tip_lamports",0)))
                p["fees"].append(float(j.get("dex_fee",0)))
                p["cu"].append(float(j.get("cu",0)))
                p["slip"].append(float(j.get("slippage_bps",0)))
                p["ev"].append(int(j.get("delta",0)))
            out={
                "median": {"tip": median(tips), "fee": median(fees), "cu": median(cu), "slip_bps": median(slip)},
                "per_pair": {k: {
                    "tip": median(v["tips"]), "fee": median(v["fees"]), "cu": median(v["cu"]), "slip_bps": median(v["slip"]),
                    "ev_med": median(v["ev"])
                } for k,v in by_pair.items()}
            }
            r.setex("solbot:cost_model", 30, json.dumps(out))
        except Exception: pass
        time.sleep(3)

if __name__=="__main__":
    main()

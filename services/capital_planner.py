
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
TOTAL_Q0=int(os.getenv("CAP_TOTAL_Q0","6000000"))  # total base units budget
REGIONS=os.getenv("REGIONS","nj-us,sg-apac").split(",")

def roic(pair, minutes=60):
    # crude ROIC: sum EV / (#trades or size proxy)
    wins=0; loss=0; n=0
    for i in range(400):
        it=r.lindex("solbot:reconcile", i)
        if not it: break
        j=json.loads(it)
        if j.get("pair")==pair:
            n+=1
            d=int(j.get("delta",0))
            if d>0: wins+=d
            else: loss+=-d
    denom=max(1, n)
    return (wins-loss)/denom

def main():
    print("[capital_planner] running")
    pairs=["SOL_USDC","JUP_USDC","WIF_USDC","BONK_USDC"]
    weights={p:1.0 for p in pairs}
    while True:
        try:
            # weight by recent ROIC + AI p_win
            ev=json.loads(r.get("solbot:ev_pred") or b'{}').get("p_win",0.5)
            s=0.0
            for p in pairs:
                w=max(0.1, 0.5*roic(p)+0.5*ev)
                weights[p]=w; s+=w
            alloc_pair={p:int(TOTAL_Q0*(weights[p]/s)) for p in pairs}
            # split half-half per region by default
            alloc_region={reg:{p:int(v/len(REGIONS)) for p,v in alloc_pair.items()} for reg in REGIONS}
            r.setex("solbot:capplan:pair", 30, json.dumps(alloc_pair))
            r.setex("solbot:capplan:region", 30, json.dumps(alloc_region))
        except Exception: pass
        time.sleep(5)

if __name__=="__main__":
    main()

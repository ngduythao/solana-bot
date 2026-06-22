
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
BASE_SIZE=int(os.getenv("BASE_SIZE_Q0","500000"))  # 0.5 units by default
MAX_MULT=float(os.getenv("ALLOC_MAX_MULT","3.0"))
MIN_MULT=float(os.getenv("ALLOC_MIN_MULT","0.2"))
def score_pair(pair):
    # Combine recent win ratio + AI EV p_win (global) as proxy
    wins=0; tot=0
    for i in range(60):
        it=r.lindex("solbot:reconcile", i)
        if not it: break
        j=json.loads(it); 
        if j.get("pair")==pair:
            tot+=1; wins += 1 if int(j.get("delta",0))>0 else 0
    wr = wins/max(1,tot)
    ev = json.loads(r.get("solbot:ev_pred") or b'{}').get("p_win", 0.5)
    return 0.5*wr + 0.5*ev
def main():
    print("[allocator] running")
    pairs=["SOL_USDC","JUP_USDC","WIF_USDC","BONK_USDC"]
    while True:
        try:
            alloc={}
            for p in pairs:
                s=score_pair(p)
                mult = max(MIN_MULT, min(MAX_MULT, 0.5 + s*1.5))
                alloc[p]=int(BASE_SIZE*mult)
            r.setex("solbot:alloc:size_q0", 20, json.dumps(alloc))
        except Exception: pass
        time.sleep(2)
if __name__=="__main__":
    main()


import os, time, json, redis, statistics
from services.common.secrets import load_system_env

load_system_env()
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

TARGET_ACCEPT = float(os.getenv("PAL_TARGET_ACCEPT","0.55"))
EV_TARGET = int(os.getenv("PAL_TARGET_EV","200000"))
ALPHA_BOUNDS=(0.9, 2.5); DP95_BOUNDS=(0.05,0.35)

ROLLBACK_HORIZON=10  # minutes to remember last good params
STATE_KEY="solbot:pal2:state"; SUG_KEY="solbot:fee_policy:suggest"

def med(a): 
    try: return statistics.median(a) if a else 0
    except: return 0

def lane_stats():
    out={}
    for k in r.scan_iter(match="jito:relay_stats:*"):
        kd=k.decode()
        if kd.endswith(":leaders"): continue
        h=r.hgetall(k)
        try:
            cnt=int(h.get(b'count',b'0') or 0); suc=int(h.get(b'success',b'0') or 0)
            p50=float(h.get(b'p50_ms',b'0') or 0); p95=float(h.get(b'p95_ms',b'0') or 0)
            acc = (suc/cnt) if cnt>0 else 0.0
            out[kd]={"acc":acc,"tail": (p95/p50) if p50>0 else 1.0}
        except: pass
    return out

def ev_recent(n=60):
    arr=[]
    for i in range(n):
        it=r.lindex("solbot:reconcile", i)
        if not it: break
        try: arr.append(json.loads(it).get("delta",0))
        except: pass
    return arr

def clamp(x, lo, hi): return max(lo, min(hi, x))

def main():
    # load last or start with env
    st=json.loads(r.get(STATE_KEY) or b'{}')
    alpha=float(st.get("alpha", os.getenv("FEE_ALPHA","1.5")))
    dp95=float(st.get("delta_p95", os.getenv("FEE_DELTA_P95","0.10")))
    last_good={"alpha":alpha,"delta_p95":dp95,"ts":time.time()}
    print("[pal2] lane-aware running")
    while True:
        try:
            lanes = lane_stats()
            acc_med = med([v["acc"] for v in lanes.values()])
            tail_med= med([v["tail"] for v in lanes.values()])
            ev_med = med(ev_recent(80))
            # adjust alpha for EV and accept%
            alpha *= 1.02 if ev_med < EV_TARGET else 0.995
            alpha *= 1.02 if acc_med < TARGET_ACCEPT else 0.995
            alpha = clamp(alpha, *ALPHA_BOUNDS)
            # tail control
            if tail_med>1.8: dp95 = clamp(float(dp95)*1.05, *DP95_BOUNDS)
            else: dp95 = clamp(float(dp95)*0.98, *DP95_BOUNDS)
            sug={"alpha":round(float(alpha),3),"beta":float(os.getenv("FEE_BETA_LAT","0.15")),
                 "gamma":float(os.getenv("FEE_GAMMA_ACC","0.25")),"delta_p95":round(float(dp95),3),
                 "acc_med":round(acc_med,3),"ev_med":int(ev_med),"tail_med":round(tail_med,3),"ts":time.time()}
            r.setex(SUG_KEY, 300, json.dumps(sug))
            r.set(STATE_KEY, json.dumps({"alpha":alpha,"delta_p95":dp95,"ts":time.time()}))
            # rollback guard: if EV plunges badly vs last 10 mins, roll back alpha/dp95
            hist = json.loads(r.get("solbot:pal2:hist") or b'[]')
            hist.append({"ev_med":ev_med,"alpha":alpha,"dp95":dp95,"ts":time.time()})
            hist = [h for h in hist if time.time()-h["ts"]<ROLLBACK_HORIZON*60]
            r.set("solbot:pal2:hist", json.dumps(hist))
            if len(hist)>=5 and ev_med < 0.5*max(h["ev_med"] for h in hist):
                alpha, dp95 = last_good["alpha"], last_good["delta_p95"]
                r.setex(SUG_KEY, 300, json.dumps({"alpha":alpha,"beta":sug["beta"],"gamma":sug["gamma"],"delta_p95":dp95,"rollback":True,"ts":time.time()}))
            else:
                last_good={"alpha":alpha,"delta_p95":dp95,"ts":time.time()}
        except Exception as e:
            print("[pal2] err", e)
        time.sleep(60)

if __name__=="__main__":
    main()

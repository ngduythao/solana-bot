
import os, time, json, redis, statistics

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

TARGET_ACCEPT = float(os.getenv("PAL_TARGET_ACCEPT","0.55"))  # 55%
EV_TARGET_LAMPORTS = int(os.getenv("PAL_TARGET_EV","200000"))  # per-bundle median target
ALPHA_BOUNDS=(0.9, 2.5)
BETA_BOUNDS=(0.05,0.4)
GAMMA_BOUNDS=(0.05,0.7)
DP95_BOUNDS=(0.05,0.35)

def rollup_accept():
    accs=[]
    for k in r.scan_iter(match="jito:relay_stats:*"):
        if k.decode().endswith(":leaders"): continue
        h=r.hgetall(k)
        try:
            cnt=int(h.get(b'count',b'0')); suc=int(h.get(b'success',b'0'))
            if cnt>0: accs.append(suc/cnt)
        except: pass
    return statistics.median(accs) if accs else 0.0

def rollup_ev(n=50):
    arr=[]
    for i in range(n):
        it=r.lindex("solbot:reconcile", i)
        if not it: break
        try:
            arr.append(json.loads(it).get("delta",0))
        except: pass
    return statistics.median(arr) if arr else 0

def clamp(x, lo, hi): return max(lo, min(hi, x))

def main():
    print("[pal] running")
    alpha=float(os.getenv("FEE_ALPHA","1.5"))
    beta =float(os.getenv("FEE_BETA_LAT","0.15"))
    gamma=float(os.getenv("FEE_GAMMA_ACC","0.25"))
    dp95=float(os.getenv("FEE_DELTA_P95","0.10"))
    while True:
        try:
            acc=rollup_accept(); ev=rollup_ev()
            # adjust alpha for EV and accept%
            if ev < EV_TARGET_LAMPORTS: alpha *= 1.04
            else: alpha *= 0.99
            if acc < TARGET_ACCEPT: alpha *= 1.03
            else: alpha *= 0.995
            alpha=clamp(alpha,*ALPHA_BOUNDS)
            # p95 tail control
            tails=[]
            for k in r.scan_iter(match="jito:relay_stats:*"):
                if k.decode().endswith(":leaders"): continue
                try:
                    p50=float(r.hget(k,"p50_ms") or 0); p95=float(r.hget(k,"p95_ms") or 0)
                    if p50>0: tails.append(p95/p50)
                except: pass
            med_tail = statistics.median(tails) if tails else 1.0
            if med_tail>1.8: dp95=clamp(dp95*1.05, *DP95_BOUNDS)
            else: dp95=clamp(dp95*0.98, *DP95_BOUNDS)
            sug={"alpha":round(alpha,3),"beta":round(beta,3),"gamma":round(gamma,3),"delta_p95":round(dp95,3),
                 "acc_med":round(acc,3),"ev_med":int(ev),"ts":time.time()}
            r.setex("solbot:fee_policy:suggest", 300, json.dumps(sug))
            print("[pal] suggest", sug)
        except Exception as e:
            print("[pal] err", e)
        time.sleep(60)
if __name__=="__main__":
    main()

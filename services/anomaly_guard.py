
import os, time, json, redis, statistics
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def robust_z(x, arr):
    if not arr: return 0.0
    med = statistics.median(arr); mad = statistics.median([abs(v-med) for v in arr]) or 1.0
    return (x-med)/(1.4826*mad)

def main():
    print("[anomaly_guard] running")
    while True:
        try:
            evs=[]; 
            for i in range(120):
                it=r.lindex("solbot:reconcile", i)
                if not it: break
                evs.append(int(json.loads(it).get("delta",0)))
            ev_med = statistics.median(evs) if evs else 0
            # accept% across relays (approx)
            accs=[]
            for k in r.scan_iter(match="jito:relay_stats:*"):
                h=r.hgetall(k)
                try: cnt=int(h.get(b'count',b'0') or 0); suc=int(h.get(b'success',b'0') or 0)
                except: continue
                if cnt>0: accs.append(suc/cnt)
            acc_med = statistics.median(accs) if accs else 0.0
            # tail ratio
            tails=[]
            for k in r.scan_iter(match="jito:relay_stats:*"):
                h=r.hgetall(k)
                try:
                    p50=float(h.get(b'p50_ms',b'0') or 0); p95=float(h.get(b'p95_ms',b'0') or 0)
                    if p50>0: tails.append(p95/p50)
                except: pass
            tail_med=statistics.median(tails) if tails else 1.0
            # z-scores
            z_ev = robust_z(ev_med, evs[-40:])
            z_acc= robust_z(acc_med, accs[-10:] if accs else [acc_med])
            z_tail= robust_z(tail_med, tails[-10:] if tails else [tail_med])
            alert = (z_ev < -2.5) or (z_acc < -2.5) or (z_tail > 3.0)
            r.setex("solbot:anomaly", 60, json.dumps({"ev_med":ev_med,"acc_med":acc_med,"tail_med":tail_med,"z":{"ev":z_ev,"acc":z_acc,"tail":z_tail},"alert":alert,"ts":time.time()}))
        except Exception: pass
        time.sleep(5)

if __name__ == "__main__":
    main()

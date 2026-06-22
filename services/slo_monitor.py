
import os, time, json, redis, statistics

r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
P99_TARGET_MS = int(os.getenv("SLO_P99_MS","1200"))
MISS_SLOT_MAX = float(os.getenv("SLO_MISS_SLOT","0.15"))

def p99(arr):
    if not arr: return 0
    arr=sorted(arr); i=int(0.99*len(arr))-1; i=max(0,min(len(arr)-1,i))
    return arr[i]

def main():
    print("[slo] running")
    while True:
        try:
            lats=[]; miss=0; total=0
            for k in r.scan_iter(match="jito:relay_stats:*"):
                kd=k.decode()
                if kd.endswith(":leaders"): continue
                h=r.hgetall(k)
                try:
                    p95=float(h.get(b"p95_ms",b"0") or 0); lats.append(p95)
                    total+=int(h.get(b"count",b"0") or 0); miss+=int(h.get(b"miss",b"0") or 0)
                except: pass
            p99_est = p99(lats)
            miss_rate = (miss/total) if total>0 else 0.0
            slo_ok = (p99_est <= P99_TARGET_MS) and (miss_rate <= MISS_SLOT_MAX)
            r.setex("solbot:slo", 120, json.dumps({"p99_ms":p99_est,"miss_rate":miss_rate,"ok":slo_ok}))
            # simple relay rotation hint: mark slow relays
            for k in r.scan_iter(match="jito:relay_stats:*"):
                kd=k.decode()
                if kd.endswith(":leaders"): continue
                try:
                    p95=float(r.hget(k,"p95_ms") or 0)
                    if p95> P99_TARGET_MS:
                        r.setex(f"relay:disable:{kd}", 60, "1")
                except: pass
        except Exception as e:
            pass
        time.sleep(10)

if __name__ == "__main__":
    main()

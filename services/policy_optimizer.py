
import os, time, json, redis, statistics

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

def read_accept(relay: str):
    h = r.hgetall(f"jito:relay_stats:{relay}")
    try:
        count = int(h.get(b"count", b"0"))
        succ = int(h.get(b"success", b"0"))
        acc = succ/count if count>0 else 0.0
    except Exception:
        acc = 0.0
    p50 = float(h.get(b"p50_ms", b"30"))
    p95 = float(h.get(b"p95_ms", b"60"))
    return acc, p50, p95

def read_reconcile_stats(n=100):
    arr = []
    for i in range(n):
        it = r.lindex("solbot:reconcile", i)
        if not it: break
        try:
            arr.append(json.loads(it))
        except Exception:
            pass
    deltas = [a.get("delta",0) for a in arr]
    return deltas

def suggest_params(relays):
    deltas = read_reconcile_stats(100)
    if not deltas:
        return None
    median_delta = statistics.median(deltas)
    alpha = float(os.getenv("FEE_ALPHA","1.5"))
    beta  = float(os.getenv("FEE_BETA_LAT","0.15"))
    gamma = float(os.getenv("FEE_GAMMA_ACC","0.25"))
    dp95  = float(os.getenv("FEE_DELTA_P95","0.10"))
    if median_delta < 0:
        alpha *= 1.05
    else:
        alpha *= 0.98
    tail = []
    for rel in relays:
        acc,p50,p95 = read_accept(rel)
        if p50>0: tail.append(p95/p50)
    if tail and statistics.median(tail) > 1.8:
        dp95 = min(0.25, dp95*1.05)
    else:
        dp95 = max(0.05, dp95*0.98)
    out = {"alpha": round(alpha,3), "beta": beta, "gamma": gamma, "delta_p95": round(dp95,3), "median_delta": median_delta}
    r.setex("solbot:fee_policy:suggest", 300, json.dumps(out))
    return out

def main():
    print("[optimizer] running")
    while True:
        try:
            relays = [k.decode().split(":")[-1] for k in r.scan_iter(match="jito:relay_stats:*") if not k.decode().endswith(":leaders")]
            s = suggest_params(relays)
            if s:
                print("[optimizer] suggest:", s)
        except Exception as e:
            print("[optimizer] err:", e)
        time.sleep(15)

if __name__ == "__main__":
    main()

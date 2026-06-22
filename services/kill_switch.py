
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
THRESH_P95=int(os.getenv("KILL_P95_MS","1600"))
THRESH_MISS=float(os.getenv("KILL_MISS","0.4"))
def main():
    print("[kill_switch] running")
    while True:
        try:
            slo=json.loads(r.get("solbot:slo") or b'{}')
            p95=float(slo.get("p95_ms",0)); miss=float(slo.get("miss_rate",0))
            if p95>THRESH_P95 or miss>THRESH_MISS:
                r.setex("solbot:kill:all", 60, "1")
            time.sleep(3)
        except Exception: time.sleep(3)
if __name__=="__main__":
    main()

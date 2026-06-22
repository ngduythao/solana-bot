
import os, time, json, redis, random
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
ENABLE=os.getenv("CHAOS_ENABLE","0")=="1"

def main():
    if not ENABLE: 
        print("[chaos] disabled"); return
    print("[chaos] running")
    while True:
        try:
            sz = random.choice([100_000, 250_000, 500_000])
            j={"reason":"chaos","size_q0":sz,"mid_q64":1<<64,"pools":["SOL/USDC.whirlpool","SOL/USDC.raydium"]}
            r.lpush("solbot:bundle_plans", json.dumps(j)); r.ltrim("solbot:bundle_plans",0,199)
        except Exception: pass
        time.sleep(5)
if __name__=="__main__":
    main()

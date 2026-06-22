
import os, time, json, redis, random
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
ENABLE=os.getenv("STEALTH_NOISE","1")=="1"
PAIRS=["SOL_USDC","JUP_USDC","WIF_USDC","BONK_USDC"]
def main():
    if not ENABLE:
        print("[noise] disabled"); return
    print("[noise] running")
    while True:
        try:
            # Push decoy metrics that don't affect executor decisions (unique keyspace)
            j={"pair": random.choice(PAIRS), "x": random.random(), "ts": time.time()}
            r.lpush("solbot:decoy:metrics", json.dumps(j)); r.ltrim("solbot:decoy:metrics", 0, 200)
        except Exception: pass
        time.sleep(random.uniform(0.8, 2.2))
if __name__=="__main__":
    main()


import os, time, json, redis
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
PAIRS=os.getenv("WARM_PAIRS","SOL_USDC,JUP_USDC,WIF_USDC,BONK_USDC").split(",")

def main():
    print("[warm_cache] running")
    while True:
        try:
            for p in PAIRS:
                r.setex(f"warm:touch:{p}", 120, "1")
            time.sleep(30)
        except Exception: time.sleep(5)

if __name__=="__main__":
    main()

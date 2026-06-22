
import os, json, time, redis
WHITELIST=set(os.getenv("PAIR_WHITELIST","SOL_USDC,JUP_USDC,WIF_USDC,BONK_USDC").split(","))
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def main():
    print("[pair_whitelist] running", WHITELIST)
    while True:
        try:
            plan=r.get("solbot:bundle_plan:next")
            if not plan: time.sleep(0.2); continue
            j=json.loads(plan)
            pair=j.get("pair") or j.get("symbol") or j.get("market_key","").replace("-","_")
            if pair not in WHITELIST:
                r.lpush("solbot:dropped:pair", json.dumps({"ts":time.time(),"pair":pair}))
                r.delete("solbot:bundle_plan:next")
                continue
        except Exception: pass
        time.sleep(0.2)
if __name__=="__main__":
    main()

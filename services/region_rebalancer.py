
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
REGION=os.getenv("REGION","nj-us")
def main():
    print("[region_rebalancer] running", REGION)
    while True:
        try:
            plan=json.loads(r.get("solbot:capplan:region") or b'{}').get(REGION,{})
            if plan:
                r.setex("solbot:alloc:size_q0", 20, json.dumps(plan))
        except Exception: pass
        time.sleep(3)
if __name__=="__main__":
    main()

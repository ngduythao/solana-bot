
# Consume hb:dispatch:hedge and log (stub)
import os, json, time, redis
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
SRC=os.getenv("DQ_HEDGE","hb:dispatch:hedge")
r=redis.from_url(REDIS_URL)
if __name__=="__main__":
    print("[auto_hedge_exec] start")
    while True:
        it=r.brpop(SRC, timeout=1)
        if it:
            print("[auto_hedge_exec] plan:", it[1])
        time.sleep(0.1)

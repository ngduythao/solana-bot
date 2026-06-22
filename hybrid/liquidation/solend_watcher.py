
# Placeholder liquidation watcher for Solend (Solana).
# Strategy: Poll program accounts / API to compute health factor; when near threshold, queue an opportunity.
# For now, emit heartbeat so the pipeline stays alive.

import os, time, json, redis
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE = os.getenv("LIQ_QUEUE", "hb:opps:liq")

r = redis.from_url(REDIS_URL)

if __name__=="__main__":
    i=0
    while True:
        i+=1
        hb={"ts":time.time(),"heartbeat":i}
        r.lpush(QUEUE, json.dumps({"type":"heartbeat","data":hb}))
        print("[LIQ] heartbeat", i)
        time.sleep(15)

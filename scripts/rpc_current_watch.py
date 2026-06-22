
import os, time, redis
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)
last=None
while True:
    cur = (r.get("rpc:current") or b'').decode() or None
    if cur and cur!=last:
        print("[RPC] current ->", cur)
        last=cur
    time.sleep(2)

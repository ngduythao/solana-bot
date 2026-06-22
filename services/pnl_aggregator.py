
import os, time, redis, json, math
from services.common.secrets import load_system_env
load_system_env()
r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def main():
    print("[pnl_aggregator] running")
    while True:
        try:
            # reconcile items should include 'pool' if available; infer 'default' otherwise
            pnl = {}
            for i in range(200):
                it = r.lindex("solbot:reconcile", i)
                if not it: break
                j = json.loads(it)
                pool = j.get("pool","default")
                pnl[pool] = pnl.get(pool, 0) + int(j.get("delta",0))
            r.setex("solbot:pnl:per_pool", 120, json.dumps(pnl))
            # Hourly EV heatmap (24x12 grid = 24 hours x 5-min buckets)
            hour = int(time.time()//3600) % 24
            ev = int(json.loads(r.lindex("solbot:reconcile", 0) or b'{"delta":0}')["delta"])
            grid = json.loads(r.get("solbot:ev:heatmap") or b'[]') or [[0 for _ in range(12)] for __ in range(24)]
            col = int((time.time()%3600)//300)
            grid[hour][col] = max(-1_000_000, min(1_000_000, ev))
            r.setex("solbot:ev:heatmap", 3600*6, json.dumps(grid))
        except Exception as e:
            pass
        time.sleep(60)

if __name__ == "__main__":
    main()

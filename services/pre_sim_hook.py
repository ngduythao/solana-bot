
# Pre-sim hook: when a swap event arrives, tighten quotes and enqueue a bundle request
import os, time, json, redis, random

r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def tighten_quote(ev):
    # Placeholder: use last adapter_entry + sim baseline to produce a price adjustment
    # Here we simply mark an action with small tip bump to race
    return {"tip_bump": 1.05, "size_mult": 0.8}

def main():
    print("[pre_sim] running")
    while True:
        try:
            raw = r.get("solbot:swap:last")
            if raw:
                ev = json.loads(raw)
                adj = tighten_quote(ev)
                req = {"reason":"backrun","adj":adj,"ts":time.time()}
                r.lpush("solbot:bundle_plans", json.dumps(req)); r.ltrim("solbot:bundle_plans", 0, 199)
                r.delete("solbot:swap:last")
        except Exception as e:
            pass
        time.sleep(0.5)

if __name__ == "__main__":
    main()

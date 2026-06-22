
import os, time, json, redis, hashlib, random

r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def pattern_key(req): return hashlib.sha256(json.dumps(req, sort_keys=True).encode()).hexdigest()[:16]

def main():
    print("[antiPVP] running")
    while True:
        try:
            req = r.lindex("solbot:bundle_plans", 0)
            if req:
                j = json.loads(req)
                key = pattern_key(j)
                last = r.get(f"antipvp:pat:{key}")
                if last:
                    # seen pattern => randomize plan
                    rnd = random.random()
                    j["randomize"] = {"fee_jitter": 1.0+0.05*rnd, "delay_jitter_ms": int(1+8*rnd)}
                    r.lset("solbot:bundle_plans", 0, json.dumps(j))
                r.setex(f"antipvp:pat:{key}", 60, "1")
        except Exception:
            pass
        time.sleep(0.5)

if __name__ == "__main__":
    main()

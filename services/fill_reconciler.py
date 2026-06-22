
import os, time, json, redis
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

def main():
    print("[reconciler] started")
    while True:
        try:
            # Expect executor or jito_client to push real fills to: solbot:fill_events
            ev = r.lpop("solbot:fill_events")
            if not ev:
                time.sleep(1.0); continue
            e = json.loads(ev)
            sim = r.get("solbot:cu_estimate")
            simv = json.loads(sim) if sim else {}
            diff = {
                "bundle_id": e.get("bundle_id"),
                "expected_min_out": simv.get("min_out"),
                "actual_out": e.get("amount_out"),
                "delta": (e.get("amount_out",0) - (simv.get("min_out") or 0)),
                "slot": e.get("slot"),
            }
            r.lpush("solbot:reconcile", json.dumps(diff))
            r.ltrim("solbot:reconcile", 0, 999)
            print("[reconciler]", diff)
        except Exception as ex:
            print("[reconciler] err:", ex)
            time.sleep(0.5)

if __name__ == "__main__":
    main()

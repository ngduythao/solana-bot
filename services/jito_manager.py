
import os, time, json, threading
import redis

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
RELAYS = [x.strip() for x in os.getenv("JITO_RELAYS","").split(",") if x.strip()]
API_KEYS = [x.strip() for x in os.getenv("JITO_API_KEYS","").split(",")]
CONC = int(os.getenv("JITO_CONCURRENCY","1"))
MODE = (os.getenv("JITO_MODE","rest") or "rest").lower()

def submit_bundle_to_relay(relay, bundle):
    # Placeholder: replace with real gRPC or REST client.
    # Here we just simulate "accepted" probabilistically or read ack from elsewhere.
    # Record a metric into Redis list "hsbot:bundle_events"
    ev = {"ts": time.time(), "relay": relay, "status": "accepted", "lat_ms": 5.0}
    r.lpush("hsbot:bundle_events", json.dumps(ev))
    
    # update window counters (simplified increment)
    r.incr("hsbot:bundle:accepted_window")
    return True

def worker():
    while True:
        raw = r.brpop("hsbot:bundles", timeout=1)
        if not raw: 
            continue
        _, payload = raw
        bundle = json.loads(payload)
        relays = RELAYS or ([os.getenv("JITO_ENDPOINT")] if os.getenv("JITO_ENDPOINT") else [])
        if not relays:
            # if no relay configured, mark as "skipped"
            r.lpush("hsbot:bundle_events", json.dumps({"ts": time.time(), "relay": None, "status": "skipped"}))
            continue
        # Fanout up to CONC relays in parallel
        threads = []
        for relay in relays[:max(1, CONC)]:
            t = threading.Thread(target=submit_bundle_to_relay, args=(relay, bundle))
            t.start(); threads.append(t)
        for t in threads:
            t.join()

if __name__=="__main__":
    print("[jito_manager] running; mode=", MODE, "relays=", RELAYS)
    worker()

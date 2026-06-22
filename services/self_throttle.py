
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def main():
    print("[self_throttle] running")
    while True:
        try:
            an=json.loads(r.get("solbot:anomaly") or b'{}')
            if an.get("alert"):
                r.setex("solbot:throttle:factor", 20, "0.5")  # halve size temporarily
            time.sleep(2)
        except Exception: time.sleep(2)
if __name__=="__main__":
    main()

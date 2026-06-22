
import os, json, time, redis

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
LOG="logs/alerts.jsonl"
os.makedirs("logs", exist_ok=True)

def main():
    p = r.pubsub()
    p.subscribe("hsbot:alerts")
    for msg in p.listen():
        if msg["type"] != "message": 
            continue
        try:
            data = json.loads(msg["data"])
        except Exception:
            data = {"raw": msg["data"].decode("utf-8","ignore")}
        r.lpush("hsbot:alert_log", json.dumps({"ts": time.time(), **data}))
        with open(LOG, "a") as f:
            f.write(json.dumps({"ts": time.time(), **data}) + "\n")

if __name__=="__main__":
    print("[alert_logger] listening on hsbot:alerts")
    main()

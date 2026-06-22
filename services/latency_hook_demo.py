
import os, json, time, redis

r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
SRC = os.getenv("PIPELINE_LOG","logs/pipeline.jsonl")

def follow(fname):
    with open(fname,"r") as f:
        f.seek(0,2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5); continue
            yield line

def main():
    if not os.path.exists(SRC):
        open(SRC,"a").close()
    for line in follow(SRC):
        try:
            ev = json.loads(line)
            ts_detect = ev.get("ts_detect"); ts_sim=ev.get("ts_sim"); ts_submit=ev.get("ts_submit")
            if ts_detect and ts_submit:
                r.lpush("hsbot:lat_events", json.dumps({"ts_detect": ts_detect, "ts_sim": ts_sim or ts_detect, "ts_submit": ts_submit}))
        except Exception:
            pass

if __name__=="__main__":
    print("[latency_hook_demo] watching", SRC)
    main()

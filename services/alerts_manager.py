
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def push(msg, sev="warn"):
    r.lpush("solbot:alerts", json.dumps({"ts": time.time(), "sev": sev, "msg": msg}))
    r.ltrim("solbot:alerts", 0, 200)

def main():
    print("[alerts_manager] running")
    last_cb=None
    while True:
        try:
            cb = r.get("solbot:cb:tripped")
            if cb and cb!=last_cb:
                push(f"Circuit breaker TRIPPED: {cb.decode()}", "critical")
                last_cb=cb
            # scan recent exec/jito/bridge failures
            for key in ["solbot:jup_exec","solbot:bridge:exec"]:
                arr=r.lrange(key,0,10)
                for it in arr:
                    try:
                        j=json.loads(it); 
                        if "fail" in (j.get("tag","")+j.get("kind","")):
                            push(f"{key} failure: {j}", "error")
                    except Exception: pass
        except Exception: pass
        time.sleep(5)

if __name__=="__main__":
    main()

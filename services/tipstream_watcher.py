
import os, time, json, redis
TIP_FLOOR_URL=os.getenv("TIP_FLOOR_URL","")
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

def fetch_floor():
    if not TIP_FLOOR_URL: return None
    try:
        import httpx
        with httpx.Client(timeout=2) as c:
            resp=c.get(TIP_FLOOR_URL)
            j=resp.json()
            # expect { "floor": <lamports> } or similar
            for k in ("floor","tip_floor","min"):
                if k in j: return int(j[k])
    except Exception:
        return None

def main():
    if not TIP_FLOOR_URL:
        print("[tipwatch] TIP_FLOOR_URL not set; watcher idle")
    else:
        print("[tipwatch] watching", TIP_FLOOR_URL)
    while True:
        try:
            f=fetch_floor()
            if f is not None:
                r.setex("jito:tip_floor", 10, str(int(f)))
        except Exception:
            pass
        time.sleep(2)

if __name__=="__main__":
    main()


import os, time, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

def traced():
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("TracerPid:"):
                    return int(line.split()[1]) != 0
    except Exception:
        return False
    return False

def main():
    print("[anti_debug] running")
    while True:
        try:
            if traced():
                r.setex("solbot:kill:all", 120, "1")
        except Exception: pass
        time.sleep(1)

if __name__=="__main__":
    main()

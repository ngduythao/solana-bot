
import os, time, json, shutil, psutil, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
DF_MIN=float(os.getenv("HLTH_DISK_FREE_MIN","2.0"))   # GB
MEM_MIN=float(os.getenv("HLTH_MEM_FREE_MIN","0.3"))    # GB

def main():
    print("[health_watchdog] running")
    while True:
        try:
            total, used, free = shutil.disk_usage("/")
            free_gb=free/1e9
            mem=psutil.virtual_memory()
            free_mem_gb=(mem.available)/1e9
            r.setex("solbot:health:disk_gb", 10, str(round(free_gb,2)))
            r.setex("solbot:health:mem_gb", 10, str(round(free_mem_gb,2)))
            if free_gb<DF_MIN or free_mem_gb<MEM_MIN:
                r.lpush("solbot:alerts", json.dumps({"ts": time.time(), "sev": "error", "msg": f"Low resources: disk {free_gb:.2f}GB, mem {free_mem_gb:.2f}GB"}))
                r.ltrim("solbot:alerts", 0, 200)
        except Exception:
            pass
        time.sleep(5)

if __name__=="__main__":
    main()

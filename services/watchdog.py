
import os, time, json, redis, subprocess

ENABLE = os.getenv("WATCHDOG_ENABLE","1")=="1"
INTERVAL = int(os.getenv("WATCHDOG_INTERVAL_SEC","20"))
r = redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))

CRITICAL = ["orchestrator","snapshot_collector_v2","order_executor","inventory_manager","fee_tuner","jito_manager","latency_meter"]

def docker_ps():
    out = subprocess.check_output(["/bin/sh","-lc","docker compose ps --services --filter 'status=running'"]).decode().strip().splitlines()
    return set(x.strip() for x in out if x.strip())

def check_and_alert():
    running = docker_ps()
    for name in CRITICAL:
        if name not in running:
            r.publish("hsbot:alerts", json.dumps({"type":"watchdog","svc":name,"msg":"not running"}))
            subprocess.call(["/bin/sh","-lc", f"docker compose up -d {name}"])

def main():
    if not ENABLE:
        print("[watchdog] disabled"); return
    print("[watchdog] running")
    while True:
        check_and_alert()
        time.sleep(INTERVAL)

if __name__=="__main__":
    main()

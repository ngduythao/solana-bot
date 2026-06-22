
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
ENABLE=os.getenv("BRIDGE_ENABLE","0")=="1"
def main():
    if not ENABLE:
        print("[bridge_planner] disabled"); return
    print("[bridge_planner] running")
    while True:
        try:
            plan=json.loads(r.get("solbot:rebalance:plan") or b"{}")
            if plan and plan.get("actions"):
                r.lpush("solbot:bridge:intents", json.dumps({"ts":time.time(),"actions":plan["actions"]}))
                r.ltrim("solbot:bridge:intents", 0, 100)
                r.delete("solbot:rebalance:plan")
        except Exception: pass
        time.sleep(5)
if __name__=="__main__":
    main()

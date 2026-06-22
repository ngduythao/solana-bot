
import time, os, redis, json
from dotenv import load_dotenv
load_dotenv()
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)

def run():
    i=0
    while True:
        i+=1
        # stub: periodically emit heartbeat so orchestrator stays active
        r.lpush("hsbot:backrun", json.dumps({"type":"heartbeat","i":i,"ts":time.time()}))
        print("[BACKRUN] heartbeat", i)
        time.sleep(5)

if __name__=="__main__":
    run()

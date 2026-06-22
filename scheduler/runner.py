
import os, time, httpx, redis
from dotenv import load_dotenv
load_dotenv()

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
AI_URL=os.getenv("AIFEE_URL","http://ai-fee:8092/tick")
PRIO_URL=os.getenv("PRIOFEE_URL","http://priority-fee:8093/tick")
CONG_KEY=os.getenv("NET_CONGESTION_KEY","net:congestion")

r=redis.from_url(REDIS_URL)

def estimate_congestion():
    # Placeholder heuristic: read recent bundle accept rate if available and map to congestion
    try:
        accept = float(r.get("bundle:accept_rate") or 0.7)
        cong = max(0.0, min(1.0, 1.0 - accept))  # lower accept -> higher congestion
    except:
        cong = 0.5
    r.set(CONG_KEY, cong)

if __name__=="__main__":
    print("[SCHED] start ticking bandit + priofee")
    with httpx.Client(timeout=2.0) as client:
        while True:
            estimate_congestion()
            for url in (AI_URL, PRIO_URL):
                try:
                    client.post(url)
                except Exception as e:
                    print("[SCHED] tick err", url, e)
            time.sleep(3)

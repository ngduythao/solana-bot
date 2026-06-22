
#!/usr/bin/env python3
# Regression runner: calls simulator and writes Redis deny keys for bad routes.
import os, json, time, math, redis, subprocess
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
r=redis.from_url(REDIS_URL)
ROUTES="routes.json"; SCORES="scores.json"; TTL=int(os.getenv("SIM_DENY_TTL_SEC","900"))
def run_once():
    # Expect another process to keep ROUTES updated; this runner just calls simulator and applies policy
    subprocess.run([os.path.join("simulator","clmm_dlmm_sim.py")], check=False)
    try:
        scores=json.load(open(SCORES,'r',encoding='utf-8'))
    except: scores=[]
    for s in scores:
        if float(s.get("expectedSlipP95Bps",999))>=float(os.getenv("SIM_MAX_SLIP_P95_BPS","160")):
            rid=(s.get("route") or "UNK").upper()
            r.setex(f"hsbot:route:deny:{rid}", TTL, "simulated_bad")
if __name__=="__main__":
    while True:
        run_once(); time.sleep(20)

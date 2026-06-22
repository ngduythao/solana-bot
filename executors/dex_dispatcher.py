
# Reads hb:dispatch:dex and forwards to existing executor pipeline (e.g., Redis queue the Rust executor reads)
import os, json, time, redis
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
SRC = os.getenv("DQ_DEX","hb:dispatch:dex")
DST = os.getenv("EXEC_IN_Q","hsbot:opps")  # reuse core executor ingress

r = redis.from_url(REDIS_URL)
FEE_LAM_KEY=os.getenv('FEE_LAMPORTS_KEY','fee:lamports')

if __name__=="__main__":
    print("[DEX-DISP] start (", SRC, "->", DST, ")")
    while True:
        it = r.brpop(SRC, timeout=1)
        if not it: 
            continue
        try:
            msg = json.loads(it[1])
        except:
            msg = {"raw": it[1].decode("utf-8","ignore")}
        try:
            lam = int(r.get(FEE_LAM_KEY) or 0)
            if lam>0:
                msg['priority_lamports']=lam
        except Exception:
            pass
        r.lpush(DST, json.dumps(msg))
        print("[DEX-DISP] forwarded", msg.get("type","?"))

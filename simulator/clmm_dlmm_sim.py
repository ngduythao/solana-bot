
# Minimal simulator hooks (tick/bin/partial) placeholder
# In production, integrate with on-chain pools data and tick math.
import json, os, time

BLACKLIST_FILE = "configs/route_blacklist.txt"

def ensure_blacklist_file():
    os.makedirs("configs", exist_ok=True)
    if not os.path.exists(BLACKLIST_FILE):
        open(BLACKLIST_FILE,"w").close()

def blacklist_route(route_id: str, reason: str):
    ensure_blacklist_file()
    line=f"{int(time.time())}\t{route_id}\t{reason}\n"
    with open(BLACKLIST_FILE,"a") as f: f.write(line)

def get_blacklist():
    ensure_blacklist_file()
    out=[]
    with open(BLACKLIST_FILE,"r") as f:
        for line in f:
            if not line.strip(): continue
            ts, rid, reason = line.strip().split("\t",2)
            out.append({"ts": int(ts), "route": rid, "reason": reason})
    return out

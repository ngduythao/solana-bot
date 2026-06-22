
#!/usr/bin/env bash
set -euo pipefail
OUT=${1:-/var/backups/solbot/treasury-$(date +%Y%m%d-%H%M%S).md}
mkdir -p "$(dirname "$OUT")"
python - <<'PY' "$OUT"
import os, json, redis, statistics, sys, time
out=sys.argv[1]
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def med(xs): 
    try: return statistics.median(xs) if xs else 0.0
    except: return 0.0
evs=[]; tips=[]; fees=[]; cu=[]; slip=[]; pairs={}
for i in range(500):
    it=r.lindex("solbot:reconcile", i)
    if not it: break
    j=json.loads(it)
    evs.append(int(j.get("delta",0)))
    tips.append(float(j.get("tip_lamports",0)))
    fees.append(float(j.get("dex_fee",0)))
    cu.append(float(j.get("cu",0)))
    slip.append(float(j.get("slippage_bps",0)))
    p=j.get("pair","_all")
    d=pairs.setdefault(p, {"ev":[], "tips":[], "fees":[], "slip":[]})
    d["ev"].append(int(j.get("delta",0)))
    d["tips"].append(float(j.get("tip_lamports",0)))
    d["fees"].append(float(j.get("dex_fee",0)))
    d["slip"].append(float(j.get("slippage_bps",0)))
with open(out,"w") as f:
    f.write("# Treasury Report\n\n")
    f.write(f"Time: {time.ctime()}\n")
    f.write(f"EV median: {med(evs)}  | tip med: {med(tips)}  | fee med: {med(fees)}  | slippage bps med: {med(slip)}\n\n")
    for k,v in pairs.items():
        f.write(f"## {k}\n")
        f.write(f"- EV_med={med(v['ev'])}  tip_med={med(v['tips'])}  fee_med={med(v['fees'])}  slip_med={med(v['slip'])}\n")
print("[treasury] wrote", out)
PY
echo "[treasury] saved -> $OUT"

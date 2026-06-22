
import os, csv, time, json, httpx, redis
from datetime import datetime, timedelta

REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
RPC=os.getenv("RPC_PRIMARY","http://rpc-gateway:8899")
OUT=os.getenv("BACKTEST_OUT","/app/backtest/pnl_daily.csv")
DAYS=int(os.getenv("BACKTEST_DAYS","1"))

r=redis.from_url(REDIS_URL)

def get_slot(client):
    payload={"jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"confirmed"}]}
    res=client.post(RPC,json=payload,timeout=2.5); res.raise_for_status()
    return res.json()["result"]

def fake_pnl_eval(slot)->dict:
    fee = float(r.get("hb:fee_burn:day") or 0.0)
    pnl = float(r.get("hb:pnl:day") or 0.0)
    return {"slot":slot,"gross":pnl+fee,"fee":fee,"net":pnl}

def run():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with httpx.Client() as c, open(OUT,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=["ts","slot","gross","fee","net"])
        w.writeheader()
        for i in range(DAYS*24):
            slot=get_slot(c)
            vals=fake_pnl_eval(slot)
            w.writerow({"ts":int(time.time()), **vals})
            time.sleep(1)
    print("done", OUT)

if __name__=="__main__":
    run()

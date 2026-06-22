
import os, time, json, redis
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
ARM_KEY="solbot:bridge:armed"
DAILY_BRIDGE_CAP=float(os.getenv("BRIDGE_DAILY_USDC_CAP","20000"))
RATE_LIMIT=int(os.getenv("BRIDGE_RATE_LIMIT_PER_HOUR","20"))

def now_hour(): import time; return int(time.time()//3600)
def hk(h): return f"bridge:min:{h}:count"
def dk(d): return f"bridge:day:{d}:usdc"
def today():
    import datetime as dt
    return dt.date.today().isoformat()

def armed(): v=r.get(ARM_KEY); return bool(v and v.decode()=="1")

def arm(seconds=900): r.setex(ARM_KEY, seconds, "1")

def handle_intents():
    it=r.rpop("solbot:bridge:intents")
    if not it: return
    j=json.loads(it)
    # budgets
    h=now_hour(); d=today()
    cnt=int(r.get(hk(h)) or 0)
    usd=float(r.get(dk(d)) or 0.0)
    if cnt>=RATE_LIMIT: return
    # estimate notional
    tot=0.0
    for a in j.get("actions", []):
        if a.get("asset")=="USDC": tot+=float(a.get("amount",0))
    if usd+tot>DAILY_BRIDGE_CAP: return
    if os.getenv("SIGNER_MODE","paper")!="hot" or not armed():
        # paper ack
        r.lpush("solbot:bridge:exec", json.dumps({"ts":time.time(),"paper":True,"actions":j.get("actions",[])})); r.ltrim("solbot:bridge:exec",0,200)
        return
    # TODO: call real bridge CLI/API; for now ack hot stub
    r.lpush("solbot:bridge:exec", json.dumps({"ts":time.time(),"paper":False,"actions":j.get("actions",[]),"tx":"bridge_stub"})); r.ltrim("solbot:bridge:exec",0,200)
    # account
    r.incr(hk(h)); r.incrbyfloat(dk(d), tot)

def main():
    print("[bridge_executor] running")
    while True:
        try:
            handle_intents()
        except Exception: pass
        time.sleep(3)

if __name__=="__main__":
    main()

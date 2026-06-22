
import os, time, json, redis, subprocess
r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

DAILY_CAP=float(os.getenv("BRIDGE_DAILY_USDC_CAP","20000"))
RATE_LIMIT=int(os.getenv("BRIDGE_RATE_LIMIT_PER_HOUR","20"))
ARM_KEY="solbot:bridge:armed"

def now_hour(): import time; return int(time.time()//3600)
def today(): import datetime as dt; return dt.date.today().isoformat()
def hk(h): return f"bridge:min:{h}:count"
def dk(d): return f"bridge:day:{d}:usdc"

def armed(): v=r.get(ARM_KEY); return bool(v and v.decode()=="1")

def exec_wormhole(amount_usdc:float, dst:str)->dict:
    # skeleton: call wormhole CLI (to be installed separately)
    try:
        cmd=f"worm cli transfer --amount {amount_usdc} --token usdc --dst {dst}"
        out=subprocess.check_output(cmd, shell=True, text=True)
        return {"ok": True, "tx": out.strip()[:100]}
    except Exception as e:
        return {"ok": False, "err": str(e)}

def handle_intents():
    it=r.rpop("solbot:bridge:intents")
    if not it: return
    j=json.loads(it)
    amt=0.0; dst=j.get("dst",""); acts=[]
    for a in j.get("actions",[]):
        if a.get("asset")=="USDC":
            amt+=float(a.get("amount",0))
            acts.append(a)
    h=now_hour(); d=today()
    cnt=int(r.get(hk(h)) or 0); usd=float(r.get(dk(d)) or 0.0)
    if cnt>=RATE_LIMIT or usd+amt>DAILY_CAP: return
    if os.getenv("SIGNER_MODE","paper")!="hot" or not armed():
        r.lpush("solbot:bridge:exec", json.dumps({"ts":time.time(),"paper":True,"amt":amt,"dst":dst})); r.ltrim("solbot:bridge:exec",0,200)
        return
    res=exec_wormhole(amt,dst)
    rec={"ts":time.time(),"paper":False,"amt":amt,"dst":dst}; rec.update(res)
    r.lpush("solbot:bridge:exec", json.dumps(rec)); r.ltrim("solbot:bridge:exec",0,200)
    r.incr(hk(h)); r.incrbyfloat(dk(d),amt)

def main():
    print("[wormhole_bridge] running")
    while True:
        try: handle_intents()
        except Exception: pass
        time.sleep(5)

if __name__=="__main__": main()

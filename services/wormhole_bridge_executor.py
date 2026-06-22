
import os, time, json, redis, subprocess

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))

ARM_KEY="solbot:bridge:armed"
DAILY_BRIDGE_CAP=float(os.getenv("BRIDGE_DAILY_USDC_CAP","20000"))
RATE_LIMIT=int(os.getenv("BRIDGE_RATE_LIMIT_PER_HOUR","20"))
RETRY_MAX=int(os.getenv("BRIDGE_RETRY_MAX","3"))
RETRY_BACKOFF=float(os.getenv("BRIDGE_RETRY_BACKOFF","2.0"))
DRY_RUN=os.getenv("BRIDGE_DRY_RUN","1")=="1"

WORMHOLE_CLI=os.getenv("WORMHOLE_CLI","wormhole")
SRC_CHAIN=os.getenv("WH_SRC_CHAIN","solana")
DST_CHAIN=os.getenv("WH_DST_CHAIN","solana")
SRC_WALLET=os.getenv("KEYPAIR_PATH","/etc/solbot/solana.json")
DST_WALLET=os.getenv("WH_DST_WALLET","/etc/solbot/solana.json")  # could be same

USDC_MINT=os.getenv("USDC_MINT","EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")

def now_hour(): return int(time.time()//3600)
def hk(h): return f"bridge:min:{h}:count"
def dk(d): return f"bridge:day:{d}:usdc"
def today():
    import datetime as dt
    return dt.date.today().isoformat()
def armed(): v=r.get(ARM_KEY); return bool(v and v.decode()=="1")

def can_budget(total_usdc):
    h=now_hour(); d=today()
    cnt=int(r.get(hk(h)) or 0)
    used=float(r.get(dk(d)) or 0.0)
    if cnt>=RATE_LIMIT: return False, "hour_rate_limit"
    if used+total_usdc>DAILY_BRIDGE_CAP: return False, "daily_cap"
    return True, ""

def account(total_usdc):
    h=now_hour(); d=today()
    r.incr(hk(h)); r.expire(hk(h), 7200)
    r.incrbyfloat(dk(d), total_usdc); r.expire(dk(d), 86400*2)

def log(kind, payload):
    r.lpush("solbot:bridge:exec", json.dumps({"ts":time.time(),"kind":kind, **payload}))
    r.ltrim("solbot:bridge:exec", 0, 200)

def do_wormhole_bridge_usdc(amount_usdc: float):
    # Placeholder CLI invocation; exact flags depend on installed CLI
    # We simulate a command call and capture stdout. In DRY_RUN we don't call.
    if DRY_RUN:
        return {"ok": True, "tx": "BRIDGE_DRYRUN", "fee": 0.0}
    cmd=f"{WORMHOLE_CLI} transfer --chain {SRC_CHAIN} --to-chain {DST_CHAIN} --amount {amount_usdc} --token {USDC_MINT} --wallet {SRC_WALLET}"
    try:
        out=subprocess.check_output(cmd.split(), shell=False, text=True, stderr=subprocess.STDOUT, timeout=60)
        # naive parse: look for signature-like token
        sig=None
        for tok in out.split():
            if len(tok)>40 and tok.isalnum():
                sig=tok; break
        return {"ok": True, "tx": sig or out[:80], "fee": 0.0}
    except Exception as e:
        return {"ok": False, "err": str(e)}

def handle_intents():
    it=r.rpop("solbot:bridge:intents")
    if not it: return
    plan=json.loads(it)
    acts=plan.get("actions",[])
    # sum usdc
    tot=0.0
    for a in acts:
        if a.get("asset")=="USDC":
            tot+=float(a.get("amount",0))
    ok, why = can_budget(tot)
    if not ok:
        log("budget_block", {"why": why, "amount": tot}); return
    if os.getenv("SIGNER_MODE","paper")!="hot" or not armed():
        log("paper_ack", {"amount": tot, "actions": acts}); return
    # Execute with retry/backoff
    tries=0
    while tries<RETRY_MAX:
        tries+=1
        res=do_wormhole_bridge_usdc(tot)
        if res.get("ok"):
            account(tot)
            log("bridge_ok", {"amount": tot, "tx": res.get("tx")})
            return
        else:
            log("bridge_fail", {"amount": tot, "err": res.get("err","") , "try": tries})
            time.sleep(RETRY_BACKOFF*tries)
    log("bridge_giveup", {"amount": tot})

def main():
    print("[wormhole_bridge_executor] running (dry_run=%s)"%DRY_RUN)
    while True:
        try:
            handle_intents()
        except Exception as e:
            log("executor_err", {"err": str(e)})
        time.sleep(3)

if __name__=="__main__":
    main()

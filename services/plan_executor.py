
import os, time, json, redis

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
MODE=os.getenv("SIGNER_MODE","paper").lower()  # 'paper' or 'hot'
KEYPATH=os.getenv("KEYPAIR_PATH","/etc/solbot/solana.json")

def log(ev, payload):
    r.lpush(f"solbot:executor:{ev}", json.dumps({"ts": time.time(), **payload}))
    r.ltrim(f"solbot:executor:{ev}", 0, 500)

def apply_paper(tag):
    # In paper mode, just mark as executed
    log("paper_exec", {"tag": tag})

def handle_gas():
    j=json.loads(r.get("solbot:gas_topup:plan") or b"{}")
    if not j: return
    if MODE!="hot" or not os.path.exists(KEYPATH):
        apply_paper("gas:"+json.dumps(j)); r.delete("solbot:gas_topup:plan"); return
    # TODO: implement real swap via Jupiter/SDK when keys provided
    apply_paper("gas_hot_pending:"+json.dumps(j)); r.delete("solbot:gas_topup:plan")

def handle_settle():
    j=json.loads(r.get("solbot:treasury:settle") or b"{}")
    if not j: return
    if MODE!="hot" or not os.path.exists(KEYPATH):
        apply_paper("settle:"+json.dumps(j)); r.delete("solbot:treasury:settle"); return
    apply_paper("settle_hot_pending:"+json.dumps(j)); r.delete("solbot:treasury:settle")

def handle_compound():
    j=json.loads(r.get("solbot:compound:plan") or b"{}")
    if not j: return
    # In paper/hot, we at least adjust allocator target via hot budget bump
    try:
        move=float(j.get("compound_move_usdc",0.0)); decomp=float(j.get("decompound_usdc",0.0))
        hot=float(r.get("solbot:treasury:hot_usdc") or 0.0)
        hot=max(0.0, hot + move - decomp)
        r.setex("solbot:treasury:hot_usdc", 60, str(hot))
        apply_paper("compound_adjust")
        r.delete("solbot:compound:plan")
    except Exception:
        pass

def main():
    print("[plan_executor] running mode=", MODE)
    while True:
        try:
            handle_gas(); handle_settle(); handle_compound()
        except Exception:
            pass
        time.sleep(2)

if __name__=="__main__":
    main()

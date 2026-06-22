
import os, time, json, redis, random
from services import jupiter_safety as SAFE
from services import jupiter_sdk
from services import jupiter_sdk_real as JREAL

r=redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
MODE=os.getenv("SIGNER_MODE","paper").lower()   # paper | hot
RPC=os.getenv("RPC_URL","")
KEY=os.getenv("KEYPAIR_PATH","/etc/solbot/solana.json")

def fake_txsig():
    # placeholder for a tx signature
    alphabet="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz123456789"
    import random
    return "Tx"+''.join(random.choice(alphabet) for _ in range(60))

def note(tag, payload):
    r.lpush("solbot:jup_exec", json.dumps({"ts":time.time(),"tag":tag, **payload}))
    r.ltrim("solbot:jup_exec", 0, 500)

def swap_usdc_to_sol(amount_sol):
    if os.getenv('JUP_REAL','0')=='1' and MODE=='hot':
        dec=int(float(os.getenv('USDC_DECIMALS','6')))
        usdc_units=int(SAFE.usdc_equiv_from_sol(os.getenv('SOL_USDC_PRICE_HINT'), amount_sol)*(10**dec))
        return JREAL.exec_usdc_to_sol(usdc_units, float(os.getenv('SOL_USDC_PRICE_HINT','100')))
    if os.getenv('JUP_SDK_ENABLE','0')=='1' and MODE=='hot':
        sdk=jupiter_sdk.JupiterSDK(RPC, KEY)
        return jupiter_sdk.real_swap_usdc_to_sol(sdk, amount_sol)
    # Here we'd call Jupiter quote+swap; we store a stub tx
    sig=fake_txsig()
    return {"ok": True, "tx": sig, "route": "USDC->SOL", "amount_sol": amount_sol}

def swap_sol_to_usdc(amount_sol):
    if os.getenv('JUP_REAL','0')=='1' and MODE=='hot':
        return JREAL.exec_sol_to_usdc(amount_sol, float(os.getenv('SOL_USDC_PRICE_HINT','100')))
    if os.getenv('JUP_SDK_ENABLE','0')=='1' and MODE=='hot':
        sdk=jupiter_sdk.JupiterSDK(RPC, KEY)
        return jupiter_sdk.real_swap_sol_to_usdc(sdk, amount_sol)
    sig=fake_txsig()
    return {"ok": True, "tx": sig, "route": "SOL->USDC", "amount_sol": amount_sol}

def process_gas():
    # safety: allowlist + caps + arming
    
    plan=json.loads(r.get("solbot:gas_topup:plan") or b"{}")
    if not plan: return
    kind=plan.get("kind"); amt=float(plan.get("amount_sol",0.0))
    if MODE!="hot":
        note("paper_gas", {"kind":kind,"amt":amt}); r.delete("solbot:gas_topup:plan"); return
    # HOT mode — execute stub swap
        ok, why = SAFE.can_swap(SAFE.usdc_equiv_from_sol(os.getenv('SOL_USDC_PRICE_HINT'), amt), ['USDC','SOL'])
    if not ok:
        note('hot_gas_blocked', {'reason': why, 'amt': amt}); r.delete('solbot:gas_topup:plan'); return
    res=swap_usdc_to_sol(amt) if kind=='topup' else swap_sol_to_usdc(amt)
    SAFE.account(SAFE.usdc_equiv_from_sol(os.getenv('SOL_USDC_PRICE_HINT'), amt))
    note("hot_gas", {"kind":kind,"amt":amt,"res":res})
    r.delete("solbot:gas_topup:plan")

def process_settle():
    plan=json.loads(r.get("solbot:treasury:settle") or b"{}")
    if not plan: return
    amt=float(plan.get("amount_usdc",0.0))
    if MODE!="hot":
        note("paper_settle", {"amt":amt}); r.delete("solbot:treasury:settle"); return
    # In practice this might be intra-wallet accounting; we just mark executed
    note("hot_settle", {"amt":amt, "tx":"internal"}); r.delete("solbot:treasury:settle")

def process_compound():
    plan=json.loads(r.get("solbot:compound:plan") or b"{}")
    if not plan: return
    move=float(plan.get("compound_move_usdc",0.0)); decomp=float(plan.get("decompound_usdc",0.0))
    # Adjust hot/vault counters
    try:
        hot=float(r.get("solbot:treasury:hot_usdc") or 0.0)
        hot=max(0.0, hot + move - decomp)
        r.setex("solbot:treasury:hot_usdc", 120, str(hot))
        if MODE!="hot":
            note("paper_compound", {"move":move,"decomp":decomp}); r.delete("solbot:compound:plan"); return
        # HOT mode: actual transfers may be within the same wallet scope (accounting)
        note("hot_compound", {"move":move,"decomp":decomp, "tx":"internal"})
        r.delete("solbot:compound:plan")
    except Exception as e:
        note("compound_err", {"err":str(e)})

def main():
    print("[jupiter_executor] mode=", MODE)
    while True:
        try:
            process_gas(); process_settle(); process_compound()
        except Exception:
            pass
        time.sleep(2)

if __name__=="__main__":
    main()

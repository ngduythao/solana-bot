
import os, json, time, base64
from typing import Dict, Any
from services import jupiter_safety as SAFE

# Optional deps
try:
    import httpx
except Exception:
    httpx=None

# Optional signing stack
SOLANA_CLI = os.getenv("SOLANA_CLI","solana")
RPC_URL = os.getenv("RPC_URL","")
KEYPAIR_PATH=os.getenv("KEYPAIR_PATH","/etc/solbot/solana.json")

def pubkey_from_keypair(path:str)->str:
    try:
        # minimal extractor via solana CLI
        import subprocess, shlex
        cmd=f"{SOLANA_CLI} address -k {path}"
        out=subprocess.check_output(cmd, shell=True, text=True).strip()
        return out
    except Exception:
        return ""

def quote(in_mint:str, out_mint:str, amount:int, slippage_bps:int)->Dict[str,Any]:
    if httpx is None:
        return {"ok": False, "why":"httpx_missing"}
    url="https://quote-api.jup.ag/v6/quote"
    params={"inputMint":in_mint,"outputMint":out_mint,"amount":amount,"slippageBps":slippage_bps}
    assert httpx is not None, 'httpx missing';
    with httpx.Client(timeout=5) as c:
        r=c.get(url, params=params)
        if r.status_code!=200: return {"ok": False, "why": f"quote_http_{r.status_code}"}
        j=r.json()
        if "data" in j and j["data"]:
            # pick best route
            route=j["data"][0]
            return {"ok": True, "route": route}
        return {"ok": False, "why":"no_route"}

def build_swap(route:Dict[str,Any])->Dict[str,Any]:
    if httpx is None:
        return {"ok": False, "why":"httpx_missing"}
    url="https://quote-api.jup.ag/v6/swap"
    user_pk=pubkey_from_keypair(KEYPAIR_PATH)
    if not user_pk:
        return {"ok": False, "why":"pubkey_missing"}
    payload={"userPublicKey": user_pk, "wrapAndUnwrapSol": True, "quoteResponse": route}
    with httpx.Client(timeout=6) as c:
        r=c.post(url, json=payload)
        if r.status_code!=200: return {"ok": False, "why": f"swap_http_{r.status_code}", "body": r.text[:200]}
        j=r.json()
        txb64=j.get("swapTransaction")
        if not txb64: return {"ok": False, "why":"no_tx"}
        return {"ok": True, "tx_b64": txb64}

def sign_and_send(tx_b64:str)->Dict[str,Any]:
    # Fallback to solana CLI for signing & send
    try:
        import subprocess, tempfile, os, base64
        raw=base64.b64decode(tx_b64.encode())
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(raw); f.flush()
            path=f.name
        env=os.environ.copy()
        if RPC_URL: env["SOLANA_URL"]=RPC_URL
        cmd=f"{SOLANA_CLI} send -k {KEYPAIR_PATH} {path} --output json"
        out=subprocess.check_output(cmd, shell=True, env=env, text=True, stderr=subprocess.STDOUT)
        try:
            j=json.loads(out)
            sig=j.get("signature") or j.get("result") or ""
        except Exception:
            sig=out.strip()
        os.unlink(path)
        return {"ok": True, "tx": sig}
    except Exception as e:
        return {"ok": False, "why":"send_fail", "err": str(e)}

def real_swap(in_mint:str, out_mint:str, amount_units:int, slippage_bps:int)->Dict[str,Any]:
    q=quote(in_mint, out_mint, amount_units, slippage_bps)
    if not q.get("ok"): return q
    s=build_swap(q["route"])
    if not s.get("ok"): return s
    return sign_and_send(s["tx_b64"])

def exec_usdc_to_sol(usdc_units:int, sol_hint_price:float)->Dict[str,Any]:
    usdc_equiv = usdc_units/(10**int(os.getenv("USDC_DECIMALS","6")))
    ok, why = SAFE.can_swap(usdc_equiv, ["USDC","SOL"])
    if not ok: return {"ok": False, "why": why}
    res=real_swap(os.getenv("USDC_MINT","EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
                  os.getenv("SOL_MINT","So11111111111111111111111111111111111111112"),
                  usdc_units, int(os.getenv("JUP_MAX_SLIPPAGE_BPS","80")))
    if res.get("ok"): SAFE.account(usdc_equiv)
    return res

def exec_sol_to_usdc(sol_amount:float, sol_hint_price:float)->Dict[str,Any]:
    usdc_equiv = SAFE.usdc_equiv_from_sol(sol_hint_price, sol_amount)
    ok, why = SAFE.can_swap(usdc_equiv, ["USDC","SOL"])
    if not ok: return {"ok": False, "why": why}
    # route uses SOL as input; we set output roughly via usdc_equiv units for sizing
    usdc_units = int(usdc_equiv*(10**int(os.getenv("USDC_DECIMALS","6"))))
    res=real_swap(os.getenv("SOL_MINT","So11111111111111111111111111111111111111112"),
                  os.getenv("USDC_MINT","EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
                  usdc_units, int(os.getenv("JUP_MAX_SLIPPAGE_BPS","80")))
    if res.get("ok"): SAFE.account(usdc_equiv)
    return res

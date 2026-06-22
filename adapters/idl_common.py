
import os, json, base64, httpx
from typing import Any, Dict

RPC_PRIMARY = os.getenv("RPC_PRIMARY","https://api.mainnet-beta.solana.com")

def rpc(method, params):
    payload = {"jsonrpc":"2.0","id":1,"method":method,"params":params}
    with httpx.Client(timeout=float(os.getenv("RPC_TIMEOUT","2.5"))) as c:
        r = c.post(RPC_PRIMARY, json=payload)
        r.raise_for_status()
        return r.json()["result"]

def get_account_b64(pubkey: str) -> bytes:
    res = rpc("getAccountInfo", [pubkey, {"encoding":"base64"}])
    v = res.get("value")
    if not v: return b""
    return base64.b64decode(v["data"][0])

def maybe_load_idl(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path): return {}
    try:
        return json.load(open(path,"r"))
    except Exception:
        return {}

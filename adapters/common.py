
import os, httpx, base64, yaml, json, time

RPC_PRIMARY = os.getenv("RPC_PRIMARY","https://api.mainnet-beta.solana.com")
TIMEOUT = float(os.getenv("RPC_TIMEOUT","2.5"))

def rpc(method, params):
    payload = {"jsonrpc":"2.0","id":1,"method":method,"params":params}
    with httpx.Client(timeout=TIMEOUT) as c:
        r = c.post(RPC_PRIMARY, json=payload)
        r.raise_for_status()
        return r.json()["result"]

def get_account_b64(pubkey: str):
    res = rpc("getAccountInfo", [pubkey, {"encoding":"base64"}])
    v = res.get("value")
    if not v: return None
    data_b64 = v["data"][0]
    return base64.b64decode(data_b64)

def get_slot():
    try:
        return rpc("getSlot", []) or 0
    except Exception:
        return 0

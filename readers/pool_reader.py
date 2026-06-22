
import os, base64, json, httpx

RPC=os.getenv("RPC_PRIMARY","http://rpc-gateway:8899")

class ParseError(Exception): pass

def _get_account_info(client, pubkey:str):
    payload={"jsonrpc":"2.0","id":1,"method":"getAccountInfo","params":[pubkey, {"encoding":"base64"}]}
    r=client.post(RPC,json=payload,timeout=2.5)
    r.raise_for_status()
    data=r.json()["result"]["value"]
    if not data: raise ParseError("account not found")
    return base64.b64decode(data["data"][0])

def read_orca_clmm_state(client, pool_pk:str):
    raw=_get_account_info(client, pool_pk)
    return {"sqrt_price_x64": 0,"liquidity": 0,"tick_current": 0,"fee_bps": 30,"tick_spacing": 64,"ticks": []}

def read_raydium_clmm_state(client, pool_pk:str):
    raw=_get_account_info(client, pool_pk)
    return {"sqrt_price_x64": 0,"liquidity": 0,"tick_current": 0,"fee_bps": 25,"tick_spacing": 64,"ticks": []}

def read_meteora_dlmm_bins(client, pool_pk:str):
    raw=_get_account_info(client, pool_pk)
    return [{"price":1.0,"liq":0.0,"fee_bps":30}]

import httpx, base64, yaml, os
ALLOWLIST = yaml.safe_load(open(os.getenv("ALLOWLIST", "config/pool_allowlist.yaml")))

async def fetch_account(rpc_url: str, pubkey: str):
    payload = {"jsonrpc":"2.0","id":1,"method":"getAccountInfo","params":[pubkey,{"encoding":"base64"}]}
    async with httpx.AsyncClient() as client:
        r = await client.post(rpc_url, json=payload, timeout=2.5)
        r.raise_for_status()
        return r.json().get("result", {}).get("value")

async def basic_guard(rpc_url: str) -> bool:
    # If allowlist empty -> skip strict guard
    pools = (ALLOWLIST.get("raydium_pools", []) or []) + (ALLOWLIST.get("orca_pools", []) or []) + (ALLOWLIST.get("meteora_pools", []) or [])
    if not pools: return True
    ok = 0
    for pk in pools[:3]:  # sample up to 3 pools
        val = await fetch_account(rpc_url, pk)
        if not val: continue
        data_b64 = val.get("data", [None])[0]
        if not data_b64: continue
        raw = base64.b64decode(data_b64)
        if len(raw) > 128: ok += 1
    return ok > 0


import os, json, time, httpx, yaml, pathlib, subprocess
from datetime import datetime

RPC = os.getenv("RPC_PRIMARY", os.getenv("RPC", "https://api.mainnet-beta.solana.com"))
OUT_DIR = os.getenv("SNAP_DIR","/app/snapshots")

def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

async def get_account(client, addr):
    rr = await client.post(RPC, json={"jsonrpc":"2.0","id":1,"method":"getAccountInfo","params":[addr,{"encoding":"base64"}]}, timeout=5.0)
    rr.raise_for_status()
    v = rr.json()["result"]["value"]
    if not v: return None
    return v["data"][0]

def try_discover(cfg):
    tokens = cfg.get("token_pairs", [])
    if not tokens: return
    for pair in tokens:
        try:
            mA, mB = pair["mintA"], pair["mintB"]
            subprocess.run(["python","tools/discovery.py", mA, mB], check=False)
        except Exception as e:
            print("discovery failed", e)

def parse_orca(b64):
    from dex_readers.orca_whirlpool_parser import parse_whirlpool_account
    st = parse_whirlpool_account(b64)
    return {"sqrt_price_x64": st.sqrt_price_x64, "liquidity": st.liquidity, "fee_bps": st.fee_tier_bps, "tick_spacing": st.tick_spacing, "ticks":[]}

def parse_raydium(b64):
    from dex_readers.raydium_clmm_parser import parse_clmm_account_via_sdk as parse_clmm_account
    st = parse_clmm_account(b64)
    return {"sqrt_price_x64": st.sqrt_price_x64, "liquidity": st.liquidity, "fee_bps": st.fee_tier_bps, "tick_spacing": st.tick_spacing, "ticks":[]}

def parse_meteora(b64):
    from dex_readers.meteora_dlmm_parser import parse_dlmm_account_via_sdk as parse_dlmm_account
    st = parse_dlmm_account(b64)
    bins = [{"price_x64": b.price_x64, "liq": b.liq} for b in st.bins]
    return {"dlmm": {"base_fee_bps": st.base_fee_bps, "bins": bins}}

async def collect_once(cfg):
    pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient() as client:
        for p in cfg.get("pools", []):
            addr = p.get("pool_account"); ptype = p.get("type")
            if not addr: continue
            data_b64 = await get_account(client, addr)
            if not data_b64: continue
            snap = {"pair": p.get("name",""), "ts": now_iso()}
            if ptype=="orca_whirlpool": snap.update(parse_orca(data_b64))
            elif ptype=="raydium_clmm": snap.update(parse_raydium(data_b64))
            elif ptype=="meteora_dlmm": snap.update(parse_meteora(data_b64))
            else: continue
            fn = os.path.join(OUT_DIR, f"{snap['ts']}.json")
            with open(fn,"w") as f: json.dump(snap,f)
            print("saved", fn)

def main():
    cfg = yaml.safe_load(open("config/pools.yaml"))
    if not cfg.get("pools"): 
        try_discover(cfg)
        cfg = yaml.safe_load(open("config/pools.yaml"))
    itv = int(os.getenv("SNAP_INTERVAL_S","5"))
    once = os.getenv("SNAP_ONCE","0")=="1"
    if once:
        import asyncio; asyncio.run(collect_once(cfg)); return
    while True:
        import asyncio; asyncio.run(collect_once(cfg))
        time.sleep(itv)

if __name__=="__main__":
    main()


import os, time, json, yaml, redis
from adapters.whirlpool_onchain import load_whirlpool_onchain
from adapters.raydium_onchain import load_raydium_onchain
from adapters.meteora_onchain import load_meteora_onchain

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

PRESETS_PATH = os.getenv("ADAPTER_PRESETS","adapters/presets.yaml")

def load_presets():
    try:
        return yaml.safe_load(open(PRESETS_PATH)) or {}
    except Exception:
        return {}

def update_adapter_entry(sel):
    pair = sel.get("pair","SOL/USDC")
    dex = sel.get("dex","WHIRLPOOL")
    presets = load_presets()
    key = "SOL_USDC" if pair.upper() == "SOL/USDC" else pair.replace("/","_").upper()
    entry = None
    try:
        if dex in ("WHIRLPOOL","ORCA"):
            src = (presets.get("whirlpool") or {}).get(key)
            if src:
                pool, ticks = load_whirlpool_onchain(src)
                entry = {
                    "dex": "WHIRLPOOL",
                    "sqrtPriceX64": pool.sqrt_price_x64,
                    "liquidity": pool.liquidity,
                    "tickCurrent": pool.tick_current,
                    "feeBps": pool.fee_bps,
                    "tickSpacing": pool.tick_spacing,
                    "ticks": [{"index": t.index, "liquidityNet": t.liquidity_net} for t in ticks]
                }
        elif dex in ("RAYDIUM","CLMM"):
            src = (presets.get("raydium") or {}).get(key)
            if src:
                pool, ticks = load_raydium_onchain(src)
                entry = {
                    "dex": "RAYDIUM",
                    "sqrtPriceX64": pool.sqrt_price_x64,
                    "liquidity": pool.liquidity,
                    "tickCurrent": pool.tick_current,
                    "feeBps": pool.fee_bps,
                    "tickSpacing": pool.tick_spacing,
                    "ticks": [{"index": t.index, "liquidityNet": t.liquidity_net} for t in ticks]
                }
        elif dex in ("METEORA","DLMM"):
            src = (presets.get("meteora") or {}).get(key)
            if src:
                st = load_meteora_onchain(src)
                entry = {
                    "dex": "METEORA",
                    "feeBps": st.fee_bps,
                    "bins": [{"priceQ64": b.price_q64, "liqQ0": b.liq_q0} for b in st.bins]
                }
    except Exception as e:
        print("[onchain_populator] parse error:", e)
    if entry:
        sel["adapter_entry"] = entry
        r.setex("solbot:preselector:current", 30, json.dumps(sel))
        r.setex("solbot:adapter_entry:last", 60, json.dumps(entry))
        print("[onchain_populator] updated adapter_entry:", entry.get("dex"), "ticks=", len(entry.get("ticks",[])), "bins=", len(entry.get("bins",[])))

def main():
    print("[onchain_populator] running")
    while True:
        try:
            cur = r.get("solbot:preselector:current")
            if cur:
                s = json.loads(cur)
                # use existing dex if present; else default whirlpool
                if not s.get("dex"):
                    s["dex"] = "WHIRLPOOL"
                update_adapter_entry(s)
        except Exception as e:
            print("[onchain_populator] err:", e)
        time.sleep(5)

if __name__ == "__main__":
    main()

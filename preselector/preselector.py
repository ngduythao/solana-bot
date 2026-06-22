
import os, time, json, asyncio, yaml
import redis, httpx
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
JUP_BASE = os.getenv("JUP_BASE","https://quote-api.jup.ag")
r = redis.from_url(REDIS_URL)

CONFIG = yaml.safe_load(open("config.yaml"))
TOKENS = CONFIG.get("tokens",["SOL/USDC","JUP/USDC","BONK/USDC","WIF/USDC"])
RISK = CONFIG.get("risk",{}); EVCFG = CONFIG.get("ev",{}); DEXCFG = CONFIG.get("dex",{})
DEX_ALLOW = set(DEXCFG.get("dex_allowlist",[]))
ONLY_DIRECT = bool(DEXCFG.get("only_direct_routes",True))

MINTS = {
  "SOL":"So11111111111111111111111111111111111111112",
  "USDC":"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "JUP":"JUP2jxvGmG2h3zWZ1j5qS9gGZ7wS9Vt7d1b7W5HYi",
  "BONK":"DezXAZ8z7Pnrn974i1qAqE9v6zE2fqBeH5bC7Z7x8Px",
  "WIF":"WifQ1RZ1xWifxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
PAIR_MAP={
  "SOL/USDC":(MINTS["USDC"],MINTS["SOL"]),
  "JUP/USDC":(MINTS["USDC"],MINTS["JUP"]),
  "BONK/USDC":(MINTS["USDC"],MINTS["BONK"]),
  "WIF/USDC":(MINTS["USDC"],MINTS["WIF"]),
}

def estimate_ev_bps(route):
    impact_bps = abs(float(route.get("priceImpactPct",0))*10000)
    micro_edge_bps = max(0.0, 3.0 - impact_bps)
    return micro_edge_bps

async def jup_quote(client, pair, amount_usd):
    inp, out = PAIR_MAP[pair]
    params = {"inputMint": inp, "outputMint": out, "amount": int(amount_usd*1_000_000),
              "slippageBps": RISK.get("slippage_cap_bps",25), "onlyDirectRoutes": ONLY_DIRECT}
    r0 = await client.get(f"{JUP_BASE}/v6/quote", params=params, timeout=2.5)
    r0.raise_for_status()
    data=r0.json().get("data",[])
    if DEX_ALLOW:
        def ok(rt):
            mi=rt.get("marketInfos",[])
            labels={(x.get("amm") or x.get("label") or '').strip() for x in mi}
            return any(l in DEX_ALLOW for l in labels)
        data=[rt for rt in data if ok(rt)]
    return data

async def loop():
    nav = float(CONFIG.get("portfolio",{}).get("nav_usd",10000))
    cap_usd = nav * (float(RISK.get("max_nav_per_trade_bps",50))/1e4)
    size = max(50.0, cap_usd)
    async with httpx.AsyncClient() as client:
        while True:
            for pair in TOKENS:
                try:
                    routes = await jup_quote(client, pair, size)
                    if not routes: continue
                    best = routes[0]
                    ev_bps = estimate_ev_bps(best)
                    if ev_bps >= float(EVCFG.get("fire_threshold_bps",3)):
                        opp = {"pair": pair, "ts": time.time(), "size_usd": size, "ev_bps": round(ev_bps,3), "route": best}
                        r.lpush("hsbot:opps", json.dumps(opp))
                        print("[PRESELECT]", pair, ev_bps, "bps")
                except Exception as e:
                    print("[PRESELECT] error", pair, e)
            await asyncio.sleep(0.8)

if __name__=="__main__":
    asyncio.run(loop())

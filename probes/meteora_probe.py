import asyncio, httpx, statistics
async def local_depth_bps(client: httpx.AsyncClient, jup_base: str, inp: str, out: str, base_usd: float, slippage_bps: int, only_direct: bool, dex_allow: set[str]) -> dict:
    sizes = [base_usd*0.5, base_usd, base_usd*1.5]; impacts = []; routes_kept = []
    for sz in sizes:
        p = {"inputMint": inp,"outputMint": out,"amount": int(sz*1_000_000),"slippageBps": slippage_bps,"onlyDirectRoutes": only_direct}
        r = await client.get(f"{jup_base}/v6/quote", params=p, timeout=2.0); r.raise_for_status(); data = r.json().get("data", [])
        if dex_allow:
            def ok(rt):
                labels = { (x.get("amm") or x.get("label") or "").strip() for x in rt.get("marketInfos", []) }
                return any(l in dex_allow for l in labels)
            data = [rt for rt in data if ok(rt)]
        if not data: continue
        best = data[0]; impacts.append(abs(float(best.get("priceImpactPct", 0))*10000)); routes_kept.append(best)
    if not impacts: return {"median_impact_bps": None, "routes": []}
    return {"median_impact_bps": statistics.median(impacts), "routes": routes_kept}

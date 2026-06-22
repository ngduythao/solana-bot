
# Minimal simulator: returns slippage estimate and EV based on route snapshot
def simulate_route(route: dict) -> dict:
    impact_bps = abs(float(route.get("priceImpactPct",0))*10000.0)
    ev_bps = max(0.0, 3.0 - impact_bps)
    return {"ev_bps": ev_bps, "impact_bps": impact_bps}

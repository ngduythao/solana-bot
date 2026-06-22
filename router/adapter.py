
# Normalize quotes from different AMM types into a unified schema

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Leg:
    amm: str
    pool: str
    input_mint: str
    output_mint: str
    qty_in: int       # in atomic units
    min_out: int      # price-limit enforced quantity (after slippage guard)

@dataclass
class Route:
    legs: List[Leg]
    est_cu: int

def normalize_from_jup(route_json: Dict[str,Any], price_limit_bps: int) -> Route:
    mi = route_json.get("marketInfos", [])
    legs = []
    for x in mi:
        amm = (x.get("amm") or x.get("label") or "Unknown").strip()
        pool = x.get("id","")
        inp_m = x.get("inputMint"); out_m = x.get("outputMint")
        qty_in = int(x.get("inAmount", 0))
        out = int(x.get("outAmount", 0))
        # apply per-leg price-limit: reduce expected out a bit
        min_out = int(out * (1.0 - price_limit_bps/10000.0))
        legs.append(Leg(amm=amm, pool=pool, input_mint=inp_m, output_mint=out_m, qty_in=qty_in, min_out=min_out))
    # naive CU estimate per leg
    est_cu = 50000 * max(1, len(legs))
    return Route(legs=legs, est_cu=est_cu)

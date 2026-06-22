
import os, csv, json, time
from sim_clmm_dlmm import route_pnl_usd, Leg

def run_suite(cases):
    out = []
    for i, c in enumerate(cases):
        pnl = route_pnl_usd([Leg(**lg) for lg in c["legs"]], c["amount_in"], c["ref_prices"])
        out.append({"case": i, "pnl": pnl})
    return out

if __name__ == "__main__":
    cases = [
        {"amount_in": 10000, "ref_prices":[1.0, 1.03], "legs":[
            {"kind":"CLMM","fee_bps":5,"price":1.0,"liquidity":2_000_000},
            {"kind":"DLMM","fee_bps":8,"price":1.01,"liquidity":1_200_000}
        ]}
    ]
    res = run_suite(cases)
    print("== Regression report ==")
    for r in res: print(r)

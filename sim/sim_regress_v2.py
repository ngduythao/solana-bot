
# Regression harness that can be plugged into existing suite
import csv, json, os
from sim_clmm_dlmm import route_pnl_usd, Leg

def run_case(case):
    legs = [Leg(**lg) for lg in case["legs"]]
    return route_pnl_usd(legs, case["amount_in"], case["ref_prices"])

if __name__ == "__main__":
    cases = [
        {"amount_in": 1000, "ref_prices":[1.0, 1.02], "legs":[{"kind":"CLMM","fee_bps":5,"price":1.0,"liquidity":1_000_000},{"kind":"DLMM","fee_bps":8,"price":1.01,"liquidity":800_000}]}
    ]
    for c in cases:
        print("PNL:", run_case(c))

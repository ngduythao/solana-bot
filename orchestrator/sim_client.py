
import os, httpx

SIM_ENDPOINT=os.getenv("SIM_ENDPOINT","http://sim-server:9000")

class SimError(Exception): pass

def simulate_clmm(state, amount_in:int, is_token_a_in:bool, limit_tick:int=None):
    payload={"state": state, "amount_in": int(amount_in), "is_token_a_in": bool(is_token_a_in)}
    if limit_tick is not None:
        payload["limit_tick"]=int(limit_tick)
    try:
        with httpx.Client() as c:
            r=c.post(f"{SIM_ENDPOINT}/simulate/clmm", json=payload, timeout=2.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise SimError(e)

def simulate_dlmm(bins, amount_in:float, is_base_in:bool):
    payload={"bins": bins, "amount_in": float(amount_in), "is_base_in": bool(is_base_in)}
    try:
        with httpx.Client() as c:
            r=c.post(f"{SIM_ENDPOINT}/simulate/dlmm", json=payload, timeout=2.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise SimError(e)

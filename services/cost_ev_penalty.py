
import os, json, redis

r = redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"))
def cost_penalty(ev:int) -> int:
    # funding/withdraw/bridge penalties (static env-config for now)
    funding_bps = float(os.getenv("FUNDING_BPS","1.0"))
    withdraw_fee = int(os.getenv("WITHDRAW_FEE","5000"))
    bridge_fee = int(os.getenv("BRIDGE_FEE","10000"))
    pen = int(ev - (abs(ev)*funding_bps/10000) - withdraw_fee - bridge_fee)
    return pen

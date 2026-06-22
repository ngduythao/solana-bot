
import os, json, time, redis
from dotenv import load_dotenv

load_dotenv()
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379/0")
SRC=os.getenv("DQ_HEDGE","hb:dispatch:hedge")
DQ_CEX=os.getenv("DQ_CEX","hb:dispatch:cex")
DQ_DEX=os.getenv("DQ_DEX","hb:dispatch:dex")

# Mapping: token -> preferred venue/type -> symbol
# Futures for SOL; SPOT for JUP/WIF/BONK (wider support)


# ENV-driven mapping for Binance & Bybit
BIN_FUT = [s.strip().upper() for s in os.getenv("CEX_BINANCE_FUTURES","SOL,BTC,ETH").split(",") if s.strip()]
BIN_SPOT= [s.strip().upper() for s in os.getenv("CEX_BINANCE_SPOT","JUP,WIF,BONK,PYTH,JTO,APT,ARB,OP,SUI").split(",") if s.strip()]
BYB_FUT = [s.strip().upper() for s in os.getenv("CEX_BYBIT_LINEAR","SOL,BTC,ETH").split(",") if s.strip()]
BYB_SPOT= [s.strip().upper() for s in os.getenv("CEX_BYBIT_SPOT","JUP,WIF,BONK,PYTH,JTO,APT,ARB,OP,SUI").split(",") if s.strip()]

def build_map():
    m={}
    # Preference: Binance Futures > Bybit Futures > Binance Spot > Bybit Spot (can be tuned)
    for t in BIN_FUT:  m[t] = {"venue":"BINANCE","type":"FUTURES","symbol": f"{t}USDT"}
    for t in BYB_FUT:  m.setdefault(t, {"venue":"BYBIT","type":"FUTURES","symbol": f"{t}USDT"})
    for t in BIN_SPOT: m.setdefault(t, {"venue":"BINANCE","type":"SPOT","symbol": f"{t}USDT"})
    for t in BYB_SPOT: m.setdefault(t, {"venue":"BYBIT","type":"SPOT","symbol": f"{t}USDT"})
    # Ensure core futures
    for t in ("SOL","BTC","ETH"):
        m[t] = {"venue":"BINANCE","type":"FUTURES","symbol": f"{t}USDT"}
    return m

CEX_MAP = build_map()

r=redis.from_url(REDIS_URL)

def handle(msg):
    token = msg.get("token"); usd = float(msg.get("notional_usd",0))
    prefer = (msg.get("prefer") or "CEX").upper()
    reason = msg.get("reason","manual")
    if token in CEX_MAP and prefer=="CEX":
        m = CEX_MAP[token]
        out = {"type":"CEX_HEDGE","venue":m["venue"],"venue_type":m["type"],"symbol":m["symbol"],
               "side":"SELL","size_usd":usd,"reason":reason}
        r.lpush(DQ_CEX, json.dumps(out))
    else:
        r.lpush(DQ_DEX, json.dumps({"type":"DEX_HEDGE","token":token,"size_usd":usd,"reason":reason}))

if __name__=="__main__":
    print("[HEDGE-EXEC] start")
    while True:
        it=r.brpop(SRC, timeout=1)
        if not it: 
            continue
        try:
            msg=json.loads(it[1])
            handle(msg)
        except Exception as e:
            print("[HEDGE-EXEC] err", e)
        time.sleep(0.05)

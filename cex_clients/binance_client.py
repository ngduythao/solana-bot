
import os, time, hmac, hashlib, requests

BINANCE_API_KEY=(open("/run/secrets/binance_api_key").read().strip() if os.path.exists("/run/secrets/binance_api_key") else os.getenv("BINANCE_API_KEY",""))
BINANCE_API_SECRET=(open("/run/secrets/binance_api_secret").read().strip() if os.path.exists("/run/secrets/binance_api_secret") else os.getenv("BINANCE_API_SECRET",""))
BINANCE_BASE=os.getenv("BINANCE_BASE","https://api.binance.com")
BINANCE_ENABLE=os.getenv("ENABLE_BINANCE","false").lower()=="true"

def _ts(): return int(time.time()*1000)

def _sign(params: dict)->str:
    query = "&".join(f"{k}={v}" for k,v in sorted(params.items()))
    return hmac.new(BINANCE_API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def _headers():
    return {"X-MBX-APIKEY": BINANCE_API_KEY} if BINANCE_API_KEY else {}

def spot_ping()->bool:
    try:
        r=requests.get(f"{BINANCE_BASE}/api/v3/ping", timeout=2)
        return r.status_code==200
    except: return False

def account_info()->dict:
    if not (BINANCE_API_KEY and BINANCE_API_SECRET): return {"dry_run": True}
    p={"timestamp":_ts()}
    p["signature"]=_sign(p)
    r=requests.get(f"{BINANCE_BASE}/api/v3/account", params=p, headers=_headers(), timeout=5)
    if r.status_code!=200: return {"error": r.text}
    return r.json()

def place_spot_order(symbol:str, side:str, qty:float, price:float=None, order_type:str="MARKET")->dict:
    if not (BINANCE_API_KEY and BINANCE_API_SECRET): return {"dry_run": True, "symbol":symbol, "side":side, "qty":qty}
    p={"symbol":symbol,"side":side,"type":order_type,"timestamp":_ts()}
    if order_type=="MARKET":
        p["quantity"]=qty
    else:
        p["timeInForce"]="GTC"; p["quantity"]=qty; p["price"]=price
    p["signature"]=_sign(p)
    r=requests.post(f"{BINANCE_BASE}/api/v3/order", params=p, headers=_headers(), timeout=5)
    if r.status_code!=200: return {"error": r.text}
    return r.json()


import os, time, hmac, hashlib, requests, json

BYBIT_API_KEY=(open("/run/secrets/bybit_api_key").read().strip() if os.path.exists("/run/secrets/bybit_api_key") else os.getenv("BYBIT_API_KEY",""))
BYBIT_API_SECRET=(open("/run/secrets/bybit_api_secret").read().strip() if os.path.exists("/run/secrets/bybit_api_secret") else os.getenv("BYBIT_API_SECRET",""))
BYBIT_BASE=os.getenv("BYBIT_BASE","https://api.bybit.com")
BYBIT_ENABLE=os.getenv("ENABLE_BYBIT","false").lower()=="true"

def _ts(): return int(time.time()*1000)

def _sign(timestamp, method, path, query, body):
    param_str = str(timestamp) + BYBIT_API_KEY + "5000" + (body if body else "")
    signature = hmac.new(BYBIT_API_SECRET.encode(), param_str.encode(), hashlib.sha256).hexdigest()
    return signature

def _headers(body=""):
    if not BYBIT_API_KEY: return {}
    ts=_ts()
    sig=_sign(ts,"GET","", "", body)
    return {
        "X-BAPI-API-KEY": BYBIT_API_KEY,
        "X-BAPI-SIGN": sig,
        "X-BAPI-SIGN-TYPE": "2",
        "X-BAPI-TIMESTAMP": str(ts),
        "X-BAPI-RECV-WINDOW": "5000",
        "Content-Type": "application/json"
    }

def server_time()->bool:
    try:
        r=requests.get(f"{BYBIT_BASE}/v5/market/time", timeout=2)
        return r.status_code==200
    except: return False

def spot_symbols()->dict:
    if not BYBIT_API_KEY: return {"dry_run": True}
    r=requests.get(f"{BYBIT_BASE}/v5/market/instruments-info?category=spot", headers=_headers(), timeout=5)
    if r.status_code!=200: return {"error": r.text}
    return r.json()

def place_spot_order(symbol:str, side:str, qty:float, price:float=None, order_type:str="MARKET")->dict:
    if not (BYBIT_API_KEY and BYBIT_API_SECRET): return {"dry_run": True, "symbol":symbol, "side":side, "qty":qty}
    ts=_ts()
    body=json.dumps({"category":"spot","symbol":symbol,"side":side,"orderType":order_type,"qty":str(qty)})
    headers=_headers(body)
    r=requests.post(f"{BYBIT_BASE}/v5/order/create", data=body, headers=headers, timeout=5)
    if r.status_code!=200: return {"error": r.text}
    return r.json()

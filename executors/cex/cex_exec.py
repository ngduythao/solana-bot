
import os, time, json, hmac, hashlib, math
import httpx, redis
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
SRC = os.getenv("DQ_CEX","hb:dispatch:cex")
SAFE_FLAG = os.getenv("ENABLE_CEX_TRADING","false").lower()=="true"

# Fee bandit recommendation (priority fee is for on-chain, but we reuse the bandit signal as aggressiveness factor)
FEE_REC_KEY = os.getenv("FEE_REC_KEY","fee:prio_mult")  # float, default 1.0

# Binance FUTURES (USDT-M)
BIN_KEY = os.getenv("BINANCE_API_KEY","")
BIN_SEC = os.getenv("BINANCE_API_SECRET","")
BIN_FAPI = "https://fapi.binance.com"
BIN_PRICE = BIN_FAPI + "/fapi/v1/ticker/price"
BIN_ORDER = BIN_FAPI + "/fapi/v1/order"

# Bybit v5 Linear USDT-M
BYB_KEY = os.getenv("BYBIT_API_KEY","")
BYB_SEC = os.getenv("BYBIT_API_SECRET","")
BYB_API = "https://api.bybit.com"
BYB_TICKER = BYB_API + "/v5/market/tickers?category=linear&symbol={sym}"
BYB_TICKER_SPOT = BYB_API + "/v5/market/tickers?category=spot&symbol={sym}"
BYB_ORDER  = BYB_API + "/v5/order/create"

# Binance SPOT
BIN_SPOT = "https://api.binance.com"
BIN_SPOT_ORDER = BIN_SPOT + "/api/v3/order"
def sign_query(params: dict, secret: str):
    from urllib.parse import urlencode
    query = urlencode(params)
    sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + "&signature=" + sig

def binance_spot_order(client, symbol, side, quote_usdt):
    ts = now_ms()
    data = {
        "symbol": symbol,
        "side": side,                 # BUY/SELL
        "type": "MARKET",
        "quoteOrderQty": str(quote_usdt),  # spend USDT amount directly
        "timestamp": ts,
        "recvWindow": 5000,
    }
    if not (BIN_KEY and BIN_SEC and SAFE_FLAG):
        return 200, json.dumps({"mode":"DRY_RUN","data":data})
    signed = sign_query(data, BIN_SEC)
    headers = {"X-MBX-APIKEY": BIN_KEY}
    res = client.post(BIN_SPOT_ORDER, headers=headers, content=signed, timeout=5)
    return res.status_code, res.text


PRICE_CACHE_TTL = 5.0

r = redis.from_url(REDIS_URL)
_last_price = {}

def now_ms():
    return int(time.time()*1000)

def fee_mult():
    try:
        v = float(r.get(FEE_REC_KEY) or 1.0)
        if v<=0: v=1.0
        return min(v, 3.0)
    except:
        return 1.0

def get_price_binance(client, symbol):
    k = ("BIN", symbol); t = _last_price.get(k, (0,0))[0]
    if time.time()-t < PRICE_CACHE_TTL: return _last_price[k][1]
    res = client.get(BIN_PRICE, params={"symbol": symbol}, timeout=5); res.raise_for_status()
    px = float(res.json()["price"]); _last_price[k]=(time.time(), px); return px

def get_price_bybit(client, symbol):
    k = ("BYB", symbol); t = _last_price.get(k, (0,0))[0]
    if time.time()-t < PRICE_CACHE_TTL: return _last_price[k][1]
    url = BYB_TICKER.format(sym=symbol); res = client.get(url, timeout=5); res.raise_for_status()
    lst = res.json().get("result",{}).get("list",[])
    if not lst: raise RuntimeError("BYBIT no ticker")
    px = float(lst[0]["lastPrice"]); _last_price[k]=(time.time(), px); return px

def usd_to_qty(usd, px, lot=0.001):
    if px<=0: return 0.0
    qty = usd/px
    return math.floor(qty/lot)*lot

def sign_binance(params: dict, secret: str):
    query = urlencode(params)
    sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + "&signature=" + sig

def binance_order(client, symbol, side, qty, reduceOnly=False):
    ts = now_ms()
    data = {
        "symbol": symbol, "side": side, "type": "MARKET",
        "quantity": qty, "timestamp": ts, "recvWindow": 5000,
        "reduceOnly": "true" if reduceOnly else "false",
    }
    signed = sign_binance(data, BIN_SEC)
    headers = {"X-MBX-APIKEY": BIN_KEY}
    res = client.post(BIN_ORDER, headers=headers, content=signed, timeout=5)
    return res.status_code, res.text

def bybit_sign(params: dict, secret: str):
    # v5 auth: apiKey + timestamp + recvWindow + payload (alphabetical)
    # We'll use minimal fields required for MARKET order
    items = sorted((k, str(v)) for k,v in params.items())
    query = "".join(k+v for k,v in items)
    sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    return sig

def bybit_order(client, symbol, side, qty):
    ts = now_ms()
    params = {
        "category": "linear",
        "symbol": symbol,
        "side": side.capitalize(),   # Buy/Sell
        "orderType": "Market",
        "qty": str(qty),
        "timestamp": str(ts),
        "recvWindow": "5000",
        "apiKey": BYB_KEY,
    }
    params["sign"] = bybit_sign(params, BYB_SEC)
    res = client.post(BYB_ORDER, json=params, timeout=5)
    return res.status_code, res.text



def place_funding_hedge(client, venue, symbol, side, usd_size, venue_type=None):
    mult = fee_mult()
    usd_adj = usd_size * mult
    if venue=="BINANCE" and venue_type=="SPOT":
        code, txt = binance_spot_order(client, symbol, side, usd_adj)
        return {"ok": code in (200,201), "resp": txt, "mode": ("LIVE" if BIN_KEY and BIN_SEC and SAFE_FLAG else "DRY_RUN"),
                "venue":venue, "venue_type":"SPOT", "quote_usdt": usd_adj}
    if venue=="BYBIT" and venue_type=="SPOT":
        px = get_price_bybit_spot(client, symbol); qty = usd_to_qty(usd_adj, px)
        if qty<=0: return {"ok": False, "err":"qty=0", "venue":venue}
        if not (BYB_KEY and BYB_SEC and SAFE_FLAG):
            return {"ok": True, "mode":"DRY_RUN", "venue":venue, "symbol":symbol, "side":side, "qty":qty, "px":px}
        code, txt = bybit_spot_order(client, symbol, side, qty)
        return {"ok": code in (200,201), "resp": txt, "mode": "LIVE", "venue":venue, "qty":qty, "px":px, "venue_type":"SPOT"}
    if venue=="BINANCE":
        px = get_price_binance(client, symbol); qty = usd_to_qty(usd_adj, px)
        if qty<=0: return {"ok": False, "err":"qty=0", "venue":venue}
        if not (BIN_KEY and BIN_SEC and SAFE_FLAG):
            return {"ok": True, "mode":"DRY_RUN", "venue":venue, "symbol":symbol, "side":side, "qty":qty, "px":px}
        code, txt = binance_order(client, symbol, side, qty)
        return {"ok": code==200, "resp": txt, "mode": "LIVE", "venue":venue, "qty":qty, "px":px}
    elif venue=="BYBIT":
        px = get_price_bybit(client, symbol); qty = usd_to_qty(usd_adj, px)
        if qty<=0: return {"ok": False, "err":"qty=0", "venue":venue}
        if not (BYB_KEY and BYB_SEC and SAFE_FLAG):
            return {"ok": True, "mode":"DRY_RUN", "venue":venue, "symbol":symbol, "side":side, "qty":qty, "px":px}
        code, txt = bybit_order(client, symbol, side, qty)
        return {"ok": code in (200,201), "resp": txt, "mode": "LIVE", "venue":venue, "qty":qty, "px":px}
    else:
        return {"ok": False, "err": "unknown venue"}

def run():
    with httpx.Client() as client:
        safe = not SAFE_FLAG or (not BIN_KEY and not BYB_KEY)
        print("[CEX-EXEC] SAFE mode:", safe)
        while True:
            it = r.brpop(SRC, timeout=1)
            if not it: 
                continue
            msg = json.loads(it[1])
            typ = msg.get("type")
            if typ=="CEX_FUNDING":
                ex = msg.get("venue"); sym = msg.get("symbol"); size = float(msg.get("size_usd",0))
                side = "SELL" if float(msg.get("funding_pct_8h",0))>0 else "BUY"
                res = place_funding_hedge(client, ex, sym, side, size, msg.get("venue_type"))
                print("[CEX-EXEC]", res)
                # TODO: POST pnl/fee to riskcap when LIVE
            elif typ=="CEX_HEDGE":
                ex = msg.get("venue"); sym = msg.get("symbol"); side = msg.get("side","SELL"); size = float(msg.get("size_usd",0))
                res = place_funding_hedge(client, ex, sym, side, size, msg.get("venue_type"))
                print("[CEX-HEDGE]", res)
            else:
                print("[CEX-EXEC] unknown msg:", msg)

if __name__=="__main__":
    run()


def bybit_spot_order(client, symbol, side, qty_base):
    ts = now_ms()
    params = {
        "category": "spot",
        "symbol": symbol,
        "side": side.capitalize(),   # Buy/Sell
        "orderType": "Market",
        "qty": str(qty_base),
        "timestamp": str(ts),
        "recvWindow": "5000",
        "apiKey": BYB_KEY,
    }
    params["sign"] = bybit_sign(params, BYB_SEC)
    res = client.post(BYB_ORDER, json=params, timeout=5)
    return res.status_code, res.text

def get_price_bybit_spot(client, symbol):
    url = BYB_TICKER_SPOT.format(sym=symbol)
    res = client.get(url, timeout=5); res.raise_for_status()
    lst = res.json().get("result",{}).get("list",[])
    if not lst: raise RuntimeError("BYBIT spot no ticker")
    return float(lst[0]["lastPrice"])

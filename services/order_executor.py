
import os, time, json, base64, httpx, redis, math, csv
from solders.signature import Signature
from solana.rpc.api import Client
from solana.transaction import Transaction
from lib.wallet import load_keypair, pubkey_str
import yaml

REDIS_URL = os.getenv("REDIS_URL","redis://redis:6379/0")
r = redis.from_url(REDIS_URL)
def current_rpc():
    try:
        v = r.get("hsbot:cfg:rpc_primary")
        if v: return v.decode()
    except Exception:
        pass
    return os.getenv("RPC_PRIMARY") or os.getenv("HELIUS_RPC") or "https://api.mainnet-beta.solana.com"
RPC = current_rpc()
JUP = os.getenv("JUP_BASE","https://quote-api.jup.ag")
SLIPPAGE = int(os.getenv("HEDGE_SLIPPAGE_BPS","30"))
MAX_CHUNK = float(os.getenv("HEDGE_MAX_CHUNK_USD","1500"))
RETRY = int(os.getenv("HEDGE_RETRY","2"))
MIN_SWAP = float(os.getenv("MIN_SWAP_USD","10"))
PF_MULT = float(r.get("hsbot:cfg:pf_mult") or 1.0)

MINTS = {
  "SOL": "So11111111111111111111111111111111111111112",
  "USDC":"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "JUP":"JUP2jxvGmG2h3zWZ1j5qS9gGZ7wS2",  # placeholder shorten if needed
  "BONK":"DezXAZ8z7Pnrn974i1qAqE9v6zE2fqBeH5bC7Z7x8Px",
  "WIF":"WifQ1RZ1xWifxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}

def est_fee_usd():
    # rough estimate; you should replace with live CU*price and sol-usd
    sol_px = float(r.get("hsbot:price:SOL") or 150.0)
    # assume 0.00005 SOL base network + priority factor
    return (0.00005 * PF_MULT) * sol_px

def chunks(total):
    out=[]; remain=total
    while remain>0:
        sz=min(MAX_CHUNK, remain)
        out.append(sz); remain -= sz
    return out



def mint_decimals(mint):
    try:
        cli = Client(current_rpc())
        resp = cli.get_token_supply(mint)
        dec = int(resp["result"]["value"]["decimals"])
        return dec
    except Exception:
        # fallbacks
        if mint == MINTS.get("SOL"): return 9
        if mint == MINTS.get("USDC"): return 6
        return 6

def price_usd_jup(mint):
    try:
        with httpx.Client(timeout=2.0) as c:
            res = c.get(f"https://price.jup.ag/v6/price", params={"ids": mint})
            js = res.json().get("data",{})
            if js:
                k=list(js.keys())[0]; return float(js[k]["price"])
    except Exception:
        return None

def amount_units_for_usd(mint, size_usd):
    px = price_usd_jup(mint) or 1.0
    dec = mint_decimals(mint)
    tokens = float(size_usd)/max(1e-9, px)
    amt_units = int(tokens * (10**dec))
    return max(1, amt_units)



def jup_quote_hedge(inp_mint, out_mint, amount_usd):
    amt = amount_units_for_usd(inp_mint, amount_usd)
    with httpx.Client(timeout=max(HEDGE_TIMEOUTS)) as c:
        data=None
        for to in HEDGE_TIMEOUTS:
            try:
                q = c.get(f"{JUP}/v6/quote", params={
                    "inputMint": inp_mint,
                    "outputMint": out_mint,
                    "amount": amt,
                    "slippageBps": min(int(_mint_override('HEDGE_SLIPPAGE_BPS', (order.get('from_symbol') or 'BASE'), HEDGE_SLIPPAGE, int)), int(_mint_override('HEDGE_MAX_SLIPPAGE_BPS', (order.get('from_symbol') or 'BASE'), HEDGE_MAX_SLIPPAGE_BPS, int))),
                    "onlyDirectRoutes": HEDGE_ONLY_DIRECT
                }, timeout=to)
                q.raise_for_status()
                arr = q.json().get("data",[])
                if arr:
                    data = arr[0]
                    # simple min-fill check (expected amountOut is quote's outAmount / amt)
                    try:
                        out_amt = float(data.get("outAmount") or 0)
                        if out_amt/ max(1, amt) < HEDGE_MIN_FILL_PCT/100.0:
                            data=None
                            continue
                    except Exception:
                        pass
                    break
            except Exception:
                continue
        return data

def jup_quote(inp_mint, out_mint, amount_usd):
    amt = amount_units_for_usd(inp_mint, amount_usd)
    with httpx.Client(timeout=10.0) as c:
        q = c.get(f"{JUP}/v6/quote", params={
            "inputMint": inp_mint,
            "outputMint": out_mint,
            "amount": amt,
            "slippageBps": SLIPPAGE,
            "onlyDirectRoutes": True
        })
        q.raise_for_status()
        arr = q.json().get("data",[])
        return arr[0] if arr else None



def _labels_from_route(route):
    labels = {(x.get("amm") or x.get("label") or "").strip().upper() for x in route.get("marketInfos", [])}
    labels.discard("")
    return labels


def _mint_override(env_key_prefix, mint_symbol, default_val, cast=float):
    """
    Priority: Redis cfg > ENV per-mint > ENV global > default
    Redis key: hsbot:hedge:cfg:{PARAM}:{MINT}  e.g. hsbot:hedge:cfg:prio_mult:SOL
    ENV per-mint: f"{env_key_prefix}_{mint_symbol.upper()}"
    ENV global: env_key_prefix
    """
    val = None
    try:
        import redis
        _r = redis.from_url(REDIS_URL)
        param = env_key_prefix.lower().replace("HEDGE_","").lower()
        rv = _r.get(f"hsbot:hedge:cfg:{param}:{mint_symbol.upper()}")
        if rv:
            return cast((rv.decode() if isinstance(rv, (bytes, bytearray)) else rv))
        rv2 = _r.get(f"hsbot:hedge:cfg:{param}:default")
        if rv2:
            return cast((rv2.decode() if isinstance(rv2, (bytes, bytearray)) else rv2))
    except Exception:
        pass
    env_per = os.getenv(f"{env_key_prefix}_{mint_symbol.upper()}")
    if env_per not in (None, ""):
        try: return cast(env_per)
        except Exception: pass
    env_glob = os.getenv(env_key_prefix)
    if env_glob not in (None, ""):
        try: return cast(env_glob)
        except Exception: pass
    return default_val
def jup_swap(route, user_pub, prio_fee=None):
    with httpx.Client(timeout=20.0) as c:
        sw = c.post(f"{JUP}/v6/swap", json={
            "userPublicKey": user_pub,
            "wrapAndUnwrapSol": True,
            "useSharedAccounts": True,
            "quoteResponse": route,
            "prioritizationFeeLamports": int(prio_fee) if prio_fee else None,
            "asLegacyTransaction": False
        })
        sw.raise_for_status()
        data = sw.json()
        tx_b64 = data["swapTransaction"]
        return tx_b64

def send_tx(tx_b64):
    cli = Client(current_rpc())
    tx_bytes = base64.b64decode(tx_b64)
    tx = Transaction.deserialize(tx_bytes)
    kp = load_keypair()
    tx.sign(kp)
    sig = cli.send_transaction(tx, kp)["result"]
    return sig

def log_exec(row):
    os.makedirs("logs", exist_ok=True)
    path = "logs/executions.csv"
    write_header = not os.path.exists(path)
    with open(path,"a",newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ts","type","size_usd","status","sig","note"])
        if write_header: w.writeheader()
        w.writerow(row)

def load_whitelist():
    try:
        with open('config/whitelist.yaml','r') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

def validate_route(route, wl):
    if int(os.getenv('WHITELIST_ENFORCE','1'))!=1:
        return True
    mis = route.get('marketInfos',[])
    allowed_prog = set((wl.get('program_ids') or []))
    allowed_pools = set((wl.get('pool_ids') or []))
    allowed_mints = set((wl.get('mints') or []))
    for mi in mis:
        pid = (mi.get('programId') or '').strip()
        amm = (mi.get('amm') or mi.get('label') or '').strip()
        pool = (mi.get('id') or mi.get('poolId') or '').strip()
        in_m = (mi.get('inputMint') or '').strip()
        out_m = (mi.get('outputMint') or '').strip()
        if allowed_prog and pid not in allowed_prog:
            return False
        if allowed_pools and pool and pool not in allowed_pools:
            return False
        if allowed_mints and ((in_m and in_m not in allowed_mints) or (out_m and out_m not in allowed_mints)):
            return False
    return True

def handle_order(order):
    typ = order.get("type")
    size = float(order.get("size_usd",0))
    if size < max(MIN_SWAP, est_fee_usd()*2):
        log_exec({"ts": time.time(), "type": typ, "size_usd": size, "status":"skip","sig":"","note":"too_small"})
        return
    user_pub = pubkey_str()
    # route: if pre-provided use it; else quote
    inp = MINTS.get((order.get("from") or "USDC").upper(), MINTS["USDC"]) 
    out = MINTS[(order.get("to") or "USDC").upper()]
    retry = RETRY
    for part in chunks(size):
        tries = 0
        while tries <= retry:
            try:
                route = order.get("route") or jup_quote(inp, out, part)
                if not route:
                    raise RuntimeError("no_route")
                wl = load_whitelist()
                if not validate_route(route, wl):
                    raise RuntimeError("route_not_whitelisted")
                txb64 = jup_swap(route, user_pub)
                sig = send_tx(txb64)
                log_exec({"ts": time.time(),"type": typ,"size_usd": part,"status":"ok","sig":sig,"note":""})
                r.publish("hsbot:alerts", json.dumps({"type":"order_ok","sig":sig,"size":part}))
                break
            except Exception as e:
                tries += 1
                if tries > retry:
                    cause = 'unknown'
                    msg = str(e)
                    if 'Route slippage' in msg or 'price' in msg:
                        cause='slippage'
                    elif 'stale' in msg or 'blockhash' in msg:
                        cause='stale'
                    elif 'route_not_whitelisted' in msg:
                        cause='whitelist'
                    elif 'no_route' in msg:
                        cause='no_route'
                    log_exec({"ts": time.time(),"type": typ,"size_usd": part,"status":"fail","sig":"","note":msg[:120]})
                    r.incr(f"hsbot:failcause:{cause}")
                    r.publish("hsbot:alerts", json.dumps({"type":"order_fail","err":str(e)}))
                else:
                    time.sleep(0.6)

def main():
    print("[order_executor] running on", RPC)
    while True:
        raw = r.brpop("hsbot:orders", timeout=1)
        if not raw: 
            continue
        _, payload = raw
        order = json.loads(payload)
        handle_order(order)

if __name__=="__main__":
    main()

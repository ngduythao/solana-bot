import os, sys, yaml, httpx, time

CONF = "config/pyth_price_ids.yaml"
HERMES_QUERY = os.getenv("PYTH_HERMES_QUERY", "https://hermes.pyth.network/v2/price_feeds")
M = yaml.safe_load(open(CONF))

ENV_PREFIX = "PYTH_ID_"  # e.g. PYTH_ID_<UPPERCASE_MINT>=0x....

SYMBOLS = {
    "JUP2jxvGmG2h3zWZ1j5qS9gGZ7wS9Vt7d1b7W5HYi": "Crypto.JUP/USD",
    "WifQ1RZ1xWifxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx": "Crypto.WIF/USD",
}

def env_override(mint: str):
    key = ENV_PREFIX + mint.upper()
    return os.getenv(key)

def fetch_id(symbol: str):
    with httpx.Client(timeout=5.0) as c:
        r = c.get(HERMES_QUERY, params={"query": symbol})
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            return data[0].get("id")
    return None

def ensure(mint: str):
    cur = M.get(mint, "").strip() if M.get(mint) else ""
    if cur.startswith("0x") and "YOUR" not in cur:
        return cur
    # ENV first
    envv = env_override(mint)
    if envv and envv.startswith("0x"):
        M[mint] = envv; return envv
    # Resolve via Hermes (retry up to 5x)
    sym = SYMBOLS.get(mint); last=None
    for i in range(5):
        try:
            fid = fetch_id(sym)
            if fid and fid.startswith("0x"):
                M[mint] = fid; return fid
        except Exception as e:
            last = e
        time.sleep(1.5)
    raise RuntimeError(f"Cannot resolve Pyth ID for {sym}: {last}")

def main():
    jup = ensure("JUP2jxvGmG2h3zWZ1j5qS9gGZ7wS9Vt7d1b7W5HYi")
    wif = ensure("WifQ1RZ1xWifxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    with open(CONF, "w") as f:
        yaml.safe_dump(M, f, sort_keys=False)
    print("Pinned IDs ->", "JUP:", jup, "WIF:", wif)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Resolver fatal:", e, file=sys.stderr)
        sys.exit(2)


import os, json, httpx, sys, time, subprocess, yaml

JUP_TOKENS = os.getenv("JUP_TOKENS_URL","https://tokens.jup.ag/tokens?tags=verified")

def symbol_to_mint(sym: str) -> str:
    sym = sym.upper()
    with httpx.Client(timeout=5.0) as c:
        r = c.get(JUP_TOKENS)
        r.raise_for_status()
        arr = r.json()
    for it in arr:
        if (it.get("symbol","") or "").upper()==sym:
            return it["address"]
    raise SystemExit(f"Cannot resolve symbol {sym} via {JUP_TOKENS}")

def main():
    if len(sys.argv)<3:
        print("Usage: python tools/discovery_symbols.py <SYM1,SYM2> <SYM3,SYM4 or QUOTE> [cluster]")
        sys.exit(1)
    base_syms = sys.argv[1].split(",")
    quote_syms = sys.argv[2].split(",")
    cluster = sys.argv[3] if len(sys.argv)>3 else "mainnet-beta"
    # If only one quote symbol provided, pair all base against it
    pairs=[]
    if len(quote_syms)==1:
        q = quote_syms[0]
        for b in base_syms:
            pairs.append((b,q))
    else:
        for b,q in zip(base_syms, quote_syms):
            pairs.append((b,q))
    # resolve and run discovery.py
    for b,q in pairs:
        mA = symbol_to_mint(b)
        mB = symbol_to_mint(q)
        print(f"Resolved {b}/{q} -> {mA}/{mB}")
        subprocess.run(["python","tools/discovery.py", mA, mB, cluster], check=False)

if __name__=="__main__":
    main()
